from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.reservations.models import TableStatusLog
from apps.staff.utils import (
    build_concierge_deeplink,
    get_active_concierge,
    is_approved_staff,
    is_super_admin,
)

from .forms import TableForm, ZoneForm
from .models import FloorPlan, Table, Zone
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


def _build_floor_snapshot(floor_plan):
    zones = list(floor_plan.zones.order_by("sort_order", "id"))
    tables = list(
        Table.objects.filter(zone__floor_plan=floor_plan, is_visible=True)
        .select_related("zone")
        .prefetch_related("perks")
        .order_by("zone__sort_order", "code")
    )
    active_shift, active_channel = get_active_concierge(floor_plan.venue)
    general_deeplink = build_concierge_deeplink(active_channel, venue=floor_plan.venue)

    status_counts = {
        "total": len(tables),
        "available": 0,
        "reserved": 0,
        "occupied": 0,
        "blocked": 0,
    }
    zone_map = {
        z.id: {
            "id": z.id,
            "name": z.name,
            "zone_type": z.zone_type,
            "display_color": z.display_color,
            "available_count": 0,
            "total_count": 0,
        }
        for z in zones
    }

    table_items = []
    for table in tables:
        key = table.status.lower()
        if key in status_counts:
            status_counts[key] += 1
        if table.zone_id in zone_map:
            zone_map[table.zone_id]["total_count"] += 1
            if table.status == "AVAILABLE":
                zone_map[table.zone_id]["available_count"] += 1

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

    zone_stats = [zone_map[z.id] for z in zones]
    return {
        "zones": zones,
        "zone_stats": zone_stats,
        "table_items": table_items,
        "status_counts": status_counts,
        "active_shift": active_shift,
        "active_channel": active_channel,
        "general_deeplink": general_deeplink,
    }


def public_map_view(request):
    """Public 2D coordinate floor map with real-time status & One-Tap Connect modal."""
    floor_plan = _get_published_floor_plan()
    snapshot = _build_floor_snapshot(floor_plan)

    return render(
        request,
        "venue/public_map.html",
        {
            "floor_plan": floor_plan,
            "venue": floor_plan.venue,
            "zones": snapshot["zones"],
            "zone_stats": snapshot["zone_stats"],
            "table_items": snapshot["table_items"],
            "status_counts": snapshot["status_counts"],
            "active_shift": snapshot["active_shift"],
            "active_channel": snapshot["active_channel"],
            "general_deeplink": snapshot["general_deeplink"],
            "is_approved_staff": is_approved_staff(request.user),
            "is_super_admin": is_super_admin(request.user),
        },
    )


def floor_status_api_view(request):
    """Lightweight JSON endpoint powering live table status polling on /floor/."""
    floor_plan = _get_published_floor_plan()
    snapshot = _build_floor_snapshot(floor_plan)
    active_shift = snapshot["active_shift"]
    active_channel = snapshot["active_channel"]

    payload = {
        "venue": {
            "name": floor_plan.venue.name,
            "hotline": floor_plan.venue.hotline,
        },
        "floor_plan": {
            "id": floor_plan.id,
            "name": floor_plan.name,
            "canvas_width": floor_plan.canvas_width,
            "canvas_height": floor_plan.canvas_height,
        },
        "synced_at": timezone.now().isoformat(),
        "counts": snapshot["status_counts"],
        "zones": snapshot["zone_stats"],
        "concierge": {
            "on_duty": bool(active_shift),
            "staff_username": active_shift.staff.username if active_shift else None,
            "channel_display": active_channel.get_channel_type_display() if active_channel else None,
            "general_deeplink": snapshot["general_deeplink"],
        },
        "tables": [
            {
                "id": item["obj"].id,
                "code": item["obj"].code,
                "label": item["obj"].label or item["obj"].code,
                "zone_id": item["obj"].zone_id,
                "zone_name": item["obj"].zone.name,
                "capacity": item["obj"].capacity,
                "min_spend": f"{item['obj'].min_spend:.2f}",
                "shape": item["obj"].shape,
                "rotation": item["obj"].rotation,
                "status": item["obj"].status,
                "status_display": item["obj"].get_status_display(),
                "perks_text": item["perks_text"],
                "notes": item["obj"].notes,
                "deeplink": item["deeplink"],
            }
            for item in snapshot["table_items"]
        ],
    }
    response = JsonResponse(payload)
    response["Cache-Control"] = "no-store"
    return response


@login_required(login_url="login:login")
def admin_hub_view(request):
    """Approved-staff single-tap table status control hub with audit logging."""
    floor_plan = _get_published_floor_plan()
    approved = is_approved_staff(request.user)
    super_admin = is_super_admin(request.user)

    selected_zone = request.GET.get("zone", "").strip()
    selected_status = request.GET.get("status", "").strip()
    search_query = request.GET.get("q", "").strip()

    if request.method == "POST":
        next_params = {}
        for key in ("zone", "status_filter", "q"):
            val = request.POST.get(key, "").strip()
            if val:
                next_params["status" if key == "status_filter" else key] = val

        def _redirect_hub():
            base_url = redirect("venue:admin_hub").url
            if next_params:
                return redirect(f"{base_url}?{urlencode(next_params)}")
            return redirect("venue:admin_hub")

        if not approved:
            messages.error(
                request,
                "Your staff account must be APPROVED by a Super Admin before updating table statuses.",
            )
            return _redirect_hub()

        table_id = request.POST.get("table_id")
        new_status = request.POST.get("status")
        valid_statuses = dict(Table.STATUSES)
        if new_status not in valid_statuses:
            messages.error(request, "Invalid table status selected.")
            return _redirect_hub()

        table = get_object_or_404(Table, pk=table_id, zone__floor_plan=floor_plan)
        previous_status = table.status
        table.status = new_status
        table.status_updated_at = timezone.now()
        table.status_updated_by = request.user
        table.save(update_fields=["status", "status_updated_at", "status_updated_by"])

        note_text = request.POST.get("note", "").strip()[:255]
        TableStatusLog.objects.create(
            table=table,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=request.user,
            source="ADMIN_HUB",
            note=note_text,
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        messages.success(
            request,
            f"Table {table.code} updated: {previous_status} -> {new_status}.",
        )
        return _redirect_hub()

    all_tables_qs = (
        Table.objects.filter(zone__floor_plan=floor_plan)
        .select_related("zone", "status_updated_by")
        .order_by("zone__sort_order", "code")
    )
    all_tables = list(all_tables_qs)
    status_counts = {
        "total": len(all_tables),
        "available": sum(1 for t in all_tables if t.status == "AVAILABLE"),
        "reserved": sum(1 for t in all_tables if t.status == "RESERVED"),
        "occupied": sum(1 for t in all_tables if t.status == "OCCUPIED"),
        "blocked": sum(1 for t in all_tables if t.status == "BLOCKED"),
    }

    filtered_qs = all_tables_qs
    if selected_zone.isdigit():
        filtered_qs = filtered_qs.filter(zone_id=int(selected_zone))
    if selected_status in dict(Table.STATUSES):
        filtered_qs = filtered_qs.filter(status=selected_status)
    if search_query:
        filtered_qs = filtered_qs.filter(
            Q(code__icontains=search_query) | Q(label__icontains=search_query)
        )

    tables = list(filtered_qs)
    zones = floor_plan.zones.order_by("sort_order", "id")
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
            "zones": zones,
            "tables": tables,
            "status_choices": Table.STATUSES,
            "status_counts": status_counts,
            "selected_zone": selected_zone,
            "selected_status": selected_status,
            "search_query": search_query,
            "recent_logs": recent_logs,
            "is_approved_staff": approved,
            "is_super_admin": super_admin,
        },
    )


@login_required(login_url="login:login")
def spatial_manage_view(request):
    """Super Admin spatial table layout, zone management, and LAYOUT_EDIT audit logging."""
    floor_plan = _get_published_floor_plan()
    super_admin = is_super_admin(request.user)

    editing_table = None
    edit_id = request.GET.get("edit")
    if edit_id:
        editing_table = get_object_or_404(Table, pk=edit_id, zone__floor_plan=floor_plan)

    editing_zone = None
    edit_zone_id = request.GET.get("edit_zone")
    if edit_zone_id:
        editing_zone = get_object_or_404(Zone, pk=edit_zone_id, floor_plan=floor_plan)

    form = TableForm(instance=editing_table, floor_plan=floor_plan)
    zone_form = ZoneForm(instance=editing_zone, prefix="zone")

    if request.method == "POST":
        if not super_admin:
            messages.error(
                request,
                "Only approved Super Admins can create or edit floor layout tables or zones.",
            )
            return redirect("venue:spatial_manage")

        form_action = request.POST.get("form_action", "save_table")

        if form_action == "save_zone":
            zone_id = request.POST.get("zone_id")
            zone_instance = (
                get_object_or_404(Zone, pk=zone_id, floor_plan=floor_plan)
                if zone_id
                else None
            )
            zone_form = ZoneForm(request.POST, instance=zone_instance, prefix="zone")
            if zone_form.is_valid():
                saved_zone = zone_form.save(commit=False)
                saved_zone.floor_plan = floor_plan
                saved_zone.save()
                action_word = "Updated" if zone_instance else "Created"
                messages.success(
                    request,
                    f"{action_word} zone '{saved_zone.name}' ({saved_zone.get_zone_type_display()}).",
                )
                return redirect("venue:spatial_manage")
            editing_zone = zone_instance

        elif form_action == "delete_table":
            delete_id = request.POST.get("table_id")
            target_table = get_object_or_404(Table, pk=delete_id, zone__floor_plan=floor_plan)
            code = target_table.code
            try:
                target_table.delete()
                messages.success(request, f"Removed table {code} from {floor_plan.name}.")
            except ProtectedError:
                messages.error(
                    request,
                    f"Table {code} has linked reservations and cannot be deleted. Uncheck 'Visible on Public Map' to hide it instead.",
                )
            return redirect("venue:spatial_manage")

        else:
            table_id = request.POST.get("table_id")
            instance = (
                get_object_or_404(Table, pk=table_id, zone__floor_plan=floor_plan)
                if table_id
                else None
            )
            previous_status = instance.status if instance else "NEW"
            form = TableForm(request.POST, instance=instance, floor_plan=floor_plan)
            if form.is_valid():
                saved_table = form.save()
                if instance is None or saved_table.status != previous_status:
                    saved_table.status_updated_at = timezone.now()
                    saved_table.status_updated_by = request.user
                    saved_table.save(update_fields=["status_updated_at", "status_updated_by"])
                    TableStatusLog.objects.create(
                        table=saved_table,
                        previous_status=previous_status,
                        new_status=saved_table.status,
                        changed_by=request.user,
                        source="LAYOUT_EDIT",
                        note=(
                            "Table created in Spatial Floor Manager"
                            if instance is None
                            else "Status updated in Spatial Floor Manager"
                        ),
                        ip_address=request.META.get("REMOTE_ADDR"),
                    )
                action_word = "Updated" if instance else "Created"
                messages.success(
                    request,
                    f"{action_word} table {saved_table.code} ({saved_table.zone.name}).",
                )
                return redirect("venue:spatial_manage")
            editing_table = instance

    zones = floor_plan.zones.order_by("sort_order", "id")
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
            "zone_form": zone_form,
            "editing_table": editing_table,
            "editing_zone": editing_zone,
            "zones": zones,
            "tables": tables,
            "is_super_admin": super_admin,
        },
    )
