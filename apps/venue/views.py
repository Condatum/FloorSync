from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.reservations.models import TableStatusLog
from apps.staff.utils import (
    build_concierge_deeplink,
    get_active_concierge,
    is_approved_staff,
    is_super_admin,
)

from .forms import TableForm
from .models import FloorPlan, Table
from .seed import seed_nocturnal_cebu


def _get_published_floor_plan():
    floor_plan = (
        FloorPlan.objects.filter(is_published=True)
        .select_related("venue")
        .order_by("-updated_at", "-id")
        .first()
    )
    if not floor_plan:
        floor_plan = seed_nocturnal_cebu()
    return floor_plan


def public_map_view(request):
    """Public 2D coordinate floor map with real-time status & One-Tap Connect modal."""
    floor_plan = _get_published_floor_plan()
    zones = floor_plan.zones.order_by("sort_order", "id")
    tables = (
        Table.objects.filter(zone__floor_plan=floor_plan, is_visible=True)
        .select_related("zone")
        .prefetch_related("perks")
        .order_by("zone__sort_order", "code")
    )

    active_shift, active_channel = get_active_concierge(floor_plan.venue)
    general_deeplink = build_concierge_deeplink(active_channel, venue=floor_plan.venue)

    table_items = []
    for table in tables:
        perk_names = [perk.name for perk in table.perks.all()]
        table_items.append(
            {
                "obj": table,
                "perks_text": ", ".join(perk_names) if perk_names else "Standard Seating",
                "deeplink": build_concierge_deeplink(
                    active_channel, venue=floor_plan.venue, table=table
                ),
            }
        )

    return render(
        request,
        "venue/public_map.html",
        {
            "floor_plan": floor_plan,
            "venue": floor_plan.venue,
            "zones": zones,
            "table_items": table_items,
            "active_shift": active_shift,
            "active_channel": active_channel,
            "general_deeplink": general_deeplink,
            "is_approved_staff": is_approved_staff(request.user),
            "is_super_admin": is_super_admin(request.user),
        },
    )


@login_required(login_url="login:login")
def admin_hub_view(request):
    """Approved-staff single-tap table status control hub with audit logging."""
    floor_plan = _get_published_floor_plan()
    approved = is_approved_staff(request.user)
    super_admin = is_super_admin(request.user)

    if request.method == "POST":
        if not approved:
            messages.error(
                request,
                "Your staff account must be APPROVED by a Super Admin before updating table statuses.",
            )
            return redirect("venue:admin_hub")

        table_id = request.POST.get("table_id")
        new_status = request.POST.get("status")
        valid_statuses = dict(Table.STATUSES)
        if new_status not in valid_statuses:
            messages.error(request, "Invalid table status selected.")
            return redirect("venue:admin_hub")

        table = get_object_or_404(Table, pk=table_id, zone__floor_plan=floor_plan)
        previous_status = table.status
        table.status = new_status
        table.status_updated_at = timezone.now()
        table.status_updated_by = request.user
        table.save(update_fields=["status", "status_updated_at", "status_updated_by"])

        TableStatusLog.objects.create(
            table=table,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=request.user,
            source="ADMIN_HUB",
            note=request.POST.get("note", "").strip()[:255],
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        messages.success(
            request,
            f"Table {table.code} updated: {previous_status} -> {new_status}.",
        )
        return redirect("venue:admin_hub")

    tables = (
        Table.objects.filter(zone__floor_plan=floor_plan)
        .select_related("zone", "status_updated_by")
        .order_by("zone__sort_order", "code")
    )
    recent_logs = (
        TableStatusLog.objects.filter(table__zone__floor_plan=floor_plan)
        .select_related("table", "changed_by")
        .order_by("-changed_at")[:12]
    )

    return render(
        request,
        "venue/admin_hub.html",
        {
            "floor_plan": floor_plan,
            "venue": floor_plan.venue,
            "tables": tables,
            "status_choices": Table.STATUSES,
            "recent_logs": recent_logs,
            "is_approved_staff": approved,
            "is_super_admin": super_admin,
        },
    )


@login_required(login_url="login:login")
def spatial_manage_view(request):
    """Super Admin spatial table layout and attribute management."""
    floor_plan = _get_published_floor_plan()
    super_admin = is_super_admin(request.user)

    editing_table = None
    edit_id = request.GET.get("edit")
    if edit_id:
        editing_table = get_object_or_404(Table, pk=edit_id, zone__floor_plan=floor_plan)

    if request.method == "POST":
        if not super_admin:
            messages.error(
                request,
                "Only approved Super Admins can create or edit floor layout tables.",
            )
            return redirect("venue:spatial_manage")

        table_id = request.POST.get("table_id")
        instance = (
            get_object_or_404(Table, pk=table_id, zone__floor_plan=floor_plan)
            if table_id
            else None
        )
        form = TableForm(request.POST, instance=instance, floor_plan=floor_plan)
        if form.is_valid():
            saved_table = form.save()
            action_word = "Updated" if instance else "Created"
            messages.success(
                request,
                f"{action_word} table {saved_table.code} ({saved_table.zone.name}).",
            )
            return redirect("venue:spatial_manage")
        editing_table = instance
    else:
        form = TableForm(instance=editing_table, floor_plan=floor_plan)

    tables = (
        Table.objects.filter(zone__floor_plan=floor_plan)
        .select_related("zone")
        .prefetch_related("perks")
        .order_by("zone__sort_order", "code")
    )

    return render(
        request,
        "venue/spatial_manage.html",
        {
            "floor_plan": floor_plan,
            "venue": floor_plan.venue,
            "form": form,
            "editing_table": editing_table,
            "tables": tables,
            "is_super_admin": super_admin,
        },
    )
