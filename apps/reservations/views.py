import secrets
import string

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.staff.utils import is_approved_staff, is_super_admin

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


@login_required(login_url="login:login")
def reservation_list_view(request):
    """Staff-authored reservation log, creation, and status/deposit updates."""
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

    reservations = (
        Reservation.objects.select_related("table", "table__zone", "created_by")
        .order_by("-created_at")[:50]
    )

    return render(
        request,
        "reservations/list.html",
        {
            "form": form,
            "reservations": reservations,
            "status_choices": Reservation.STATUSES,
            "is_approved_staff": approved,
            "is_super_admin": is_super_admin(request.user),
        },
    )


@login_required(login_url="login:login")
def audit_log_view(request):
    """Display the TableStatusLog audit ledger."""
    logs = (
        TableStatusLog.objects.select_related("table", "table__zone", "reservation", "changed_by")
        .order_by("-changed_at")[:100]
    )

    return render(
        request,
        "reservations/audit.html",
        {
            "logs": logs,
            "is_approved_staff": is_approved_staff(request.user),
            "is_super_admin": is_super_admin(request.user),
        },
    )
