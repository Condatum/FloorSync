import csv
from decimal import Decimal
import secrets
import string
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.staff.utils import is_approved_staff, is_super_admin
from apps.venue.models import Table

from .forms import ReservationForm
from .models import Reservation, TableStatusLog

RESERVATION_TO_TABLE_STATUS = {
    "HELD": "RESERVED",
    "CONFIRMED": "RESERVED",
    "SEATED": "OCCUPIED",
    "COMPLETED": "AVAILABLE",
    "CANCELLED": "AVAILABLE",
    "NO_SHOW": "AVAILABLE",
}


def _generate_reference_code():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "FS-" + "".join(secrets.choice(alphabet) for _ in range(6))
        if not Reservation.objects.filter(reference_code=code).exists():
            return code


def _sync_table_for_reservation(reservation, user, ip_address=None):
    """Sync linked Table.status with reservation status and log any status change."""
    target_status = RESERVATION_TO_TABLE_STATUS.get(reservation.status)
    if not target_status:
        return False

    table = reservation.table
    previous_status = table.status
    if previous_status == target_status:
        return False

    table.status = target_status
    table.status_updated_at = timezone.now()
    table.status_updated_by = user
    table.save(update_fields=["status", "status_updated_at", "status_updated_by"])

    TableStatusLog.objects.create(
        table=table,
        reservation=reservation,
        previous_status=previous_status,
        new_status=target_status,
        changed_by=user,
        source="ADMIN_HUB",
        note=f"Reservation {reservation.reference_code} ({reservation.status})",
        ip_address=ip_address,
    )
    return True


def _safe_csv_cell(value):
    text = "" if value is None else str(value)
    if text and text[0] in ("=", "+", "-", "@"):
        return f"'{text}"
    return text


@login_required(login_url="login:login")
def reservation_list_view(request):
    """Staff-authored reservation log, creation, filtering, KPIs, and status/deposit updates."""
    approved = is_approved_staff(request.user)
    form = ReservationForm()

    if request.method == "POST":
        if not approved:
            messages.error(
                request,
                "Your staff account must be APPROVED by a Super Admin before creating or updating reservations.",
            )
            return redirect("reservations:list")

        action = request.POST.get("action", "create")
        ip_address = request.META.get("REMOTE_ADDR")

        if action == "update":
            reservation_id = request.POST.get("reservation_id")
            res = get_object_or_404(Reservation, pk=reservation_id)
            new_status = request.POST.get("status", res.status)
            if new_status not in dict(Reservation.STATUSES):
                messages.error(request, "Invalid reservation status selected.")
                return redirect("reservations:list")

            res.status = new_status
            res.payment_verified = request.POST.get("payment_verified") in ("on", "true", "1", "True")
            res.save(update_fields=["status", "payment_verified", "updated_at"])

            synced = _sync_table_for_reservation(res, request.user, ip_address=ip_address)
            if synced:
                messages.success(
                    request,
                    f"Updated {res.reference_code} ({res.status}) and synced Table {res.table.code} -> {res.table.status}.",
                )
            else:
                messages.success(request, f"Updated reservation {res.reference_code}.")
            return redirect("reservations:list")

        form = ReservationForm(request.POST)
        if form.is_valid():
            res = form.save(commit=False)
            res.reference_code = _generate_reference_code()
            res.created_by = request.user
            res.save()

            synced = _sync_table_for_reservation(res, request.user, ip_address=ip_address)
            if synced:
                messages.success(
                    request,
                    f"Created reservation {res.reference_code} for {res.guest_name} and set Table {res.table.code} -> {res.table.status}.",
                )
            else:
                messages.success(
                    request,
                    f"Created reservation {res.reference_code} for {res.guest_name}.",
                )
            return redirect("reservations:list")

    search_query = request.GET.get("q", "").strip()
    selected_status = request.GET.get("status", "").strip()
    selected_payment = request.GET.get("payment", "").strip()

    kpi_agg = Reservation.objects.aggregate(
        total_count=Count("id"),
        active_count=Count("id", filter=Q(status__in=["HELD", "CONFIRMED", "SEATED"])),
        verified_count=Count("id", filter=Q(payment_verified=True)),
        verified_deposit_total=Sum("deposit_amount", filter=Q(payment_verified=True)),
        seated_guests=Sum("party_size", filter=Q(status="SEATED")),
    )
    kpis = {
        "total_count": kpi_agg["total_count"] or 0,
        "active_count": kpi_agg["active_count"] or 0,
        "verified_count": kpi_agg["verified_count"] or 0,
        "verified_deposit_total": kpi_agg["verified_deposit_total"] or Decimal("0.00"),
        "seated_guests": kpi_agg["seated_guests"] or 0,
    }

    qs = Reservation.objects.select_related("table", "table__zone", "created_by")
    if search_query:
        qs = qs.filter(
            Q(reference_code__icontains=search_query)
            | Q(guest_name__icontains=search_query)
            | Q(guest_contact__icontains=search_query)
            | Q(table__code__icontains=search_query)
        )
    if selected_status in dict(Reservation.STATUSES):
        qs = qs.filter(status=selected_status)
    if selected_payment == "verified":
        qs = qs.filter(payment_verified=True)
    elif selected_payment == "pending":
        qs = qs.filter(payment_verified=False)

    reservations = qs.order_by("-created_at")[:50]

    return render(
        request,
        "reservations/list.html",
        {
            "form": form,
            "reservations": reservations,
            "status_choices": Reservation.STATUSES,
            "kpis": kpis,
            "search_query": search_query,
            "selected_status": selected_status,
            "selected_payment": selected_payment,
            "is_approved_staff": approved,
            "is_super_admin": is_super_admin(request.user),
        },
    )


@login_required(login_url="login:login")
def audit_log_view(request):
    """Display and optionally export the TableStatusLog audit ledger."""
    search_query = request.GET.get("q", "").strip()
    selected_source = request.GET.get("source", "").strip()
    selected_status = request.GET.get("status", "").strip()

    qs = TableStatusLog.objects.select_related(
        "table", "table__zone", "reservation", "changed_by"
    ).order_by("-changed_at")

    if search_query:
        qs = qs.filter(
            Q(table__code__icontains=search_query)
            | Q(note__icontains=search_query)
            | Q(changed_by__username__icontains=search_query)
            | Q(reservation__reference_code__icontains=search_query)
        )
    if selected_source in dict(TableStatusLog.SOURCES):
        qs = qs.filter(source=selected_source)
    if selected_status in dict(Table.STATUSES):
        qs = qs.filter(new_status=selected_status)

    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="floorsync_audit_ledger.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Timestamp",
                "Table",
                "Zone",
                "Previous Status",
                "New Status",
                "Source",
                "Changed By",
                "Reservation Ref",
                "IP Address",
                "Note",
            ]
        )
        for log in qs[:500]:
            writer.writerow(
                [
                    log.changed_at.strftime("%Y-%m-%d %H:%M:%S"),
                    _safe_csv_cell(log.table.code),
                    _safe_csv_cell(log.table.zone.name),
                    log.previous_status,
                    log.new_status,
                    log.get_source_display(),
                    _safe_csv_cell(log.changed_by.username if log.changed_by else "System"),
                    _safe_csv_cell(log.reservation.reference_code if log.reservation else ""),
                    log.ip_address or "",
                    _safe_csv_cell(log.note),
                ]
            )
        return response

    export_params = {"export": "csv"}
    if search_query:
        export_params["q"] = search_query
    if selected_source:
        export_params["source"] = selected_source
    if selected_status:
        export_params["status"] = selected_status

    logs = qs[:100]

    return render(
        request,
        "reservations/audit.html",
        {
            "logs": logs,
            "source_choices": TableStatusLog.SOURCES,
            "table_status_choices": Table.STATUSES,
            "search_query": search_query,
            "selected_source": selected_source,
            "selected_status": selected_status,
            "export_query": urlencode(export_params),
            "is_approved_staff": is_approved_staff(request.user),
            "is_super_admin": is_super_admin(request.user),
        },
    )
