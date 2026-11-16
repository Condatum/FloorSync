from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.venue.models import Venue

from .forms import ContactChannelForm, DutyShiftStartForm
from .models import ContactChannel, DutyShift, StaffAccount
from .utils import (
    build_concierge_deeplink,
    get_active_concierge,
    get_or_create_staff_account,
    is_approved_staff,
    is_super_admin,
)


@login_required(login_url="login:login")
def vetting_view(request):
    """Gatekeeper staff vetting screen (Super Admin approval/rejection + status view)."""
    my_account = get_or_create_staff_account(request.user)
    super_admin = is_super_admin(request.user)

    if request.method == "POST":
        if not super_admin:
            messages.error(request, "Only Super Admins can approve or modify staff verification states.")
            return redirect("staff:vetting")

        account_id = request.POST.get("account_id")
        action = request.POST.get("action")
        target = get_object_or_404(StaffAccount, pk=account_id)

        if action == "approve":
            target.verification_status = "APPROVED"
            target.verified_by = request.user
            target.verified_at = timezone.now()
            target.rejection_reason = ""
            target.save()
            messages.success(request, f"Approved staff account for '{target.user.username}'.")
        elif action == "make_super_admin":
            target.role = "SUPER_ADMIN"
            target.verification_status = "APPROVED"
            target.verified_by = request.user
            target.verified_at = timezone.now()
            target.rejection_reason = ""
            target.save()
            messages.success(request, f"Promoted '{target.user.username}' to Super Admin.")
        elif action == "reject":
            reason = request.POST.get("rejection_reason", "").strip() or "Identity verification declined."
            target.verification_status = "REJECTED"
            target.verified_by = request.user
            target.verified_at = timezone.now()
            target.rejection_reason = reason
            target.save()
            messages.info(request, f"Marked '{target.user.username}' as rejected.")

        return redirect("staff:vetting")

    accounts = StaffAccount.objects.select_related("user", "verified_by").order_by(
        "verification_status", "-requested_at"
    )
    return render(
        request,
        "staff/vetting.html",
        {
            "my_account": my_account,
            "is_super_admin": super_admin,
            "is_approved_staff": is_approved_staff(request.user),
            "accounts": accounts,
        },
    )


@login_required(login_url="login:login")
def duty_view(request):
    """Manage staff ContactChannels and active DutyShift for One-Tap Connect routing."""
    my_account = get_or_create_staff_account(request.user)
    approved = is_approved_staff(request.user)

    channel_form = ContactChannelForm(prefix="channel")
    shift_form = DutyShiftStartForm(prefix="shift", user=request.user)

    if request.method == "POST":
        if not approved:
            messages.error(request, "Your staff account must be APPROVED before managing live duty routing.")
            return redirect("staff:duty")

        form_type = request.POST.get("form_type")
        if form_type == "add_channel":
            channel_form = ContactChannelForm(request.POST, prefix="channel")
            if channel_form.is_valid():
                channel = channel_form.save(commit=False)
                channel.staff = request.user
                if channel.is_primary:
                    ContactChannel.objects.filter(staff=request.user, is_primary=True).update(is_primary=False)
                ContactChannel.objects.update_or_create(
                    staff=request.user,
                    channel_type=channel.channel_type,
                    defaults={
                        "handle_or_url": channel.handle_or_url,
                        "is_primary": channel.is_primary,
                        "is_active": channel.is_active,
                    },
                )
                messages.success(request, f"Saved {channel.get_channel_type_display()} contact channel.")
                return redirect("staff:duty")
        elif form_type == "start_shift":
            shift_form = DutyShiftStartForm(request.POST, prefix="shift", user=request.user)
            if shift_form.is_valid():
                shift = shift_form.save(commit=False)
                DutyShift.objects.filter(venue=shift.venue, is_active=True, ended_at__isnull=True).update(
                    is_active=False, ended_at=timezone.now()
                )
                shift.staff = request.user
                shift.is_active = True
                shift.save()
                messages.success(
                    request,
                    f"You are now the active on-duty concierge for {shift.venue.name}.",
                )
                return redirect("staff:duty")
        elif form_type == "end_shift":
            shift_id = request.POST.get("shift_id")
            shift = get_object_or_404(DutyShift, pk=shift_id)
            shift.is_active = False
            shift.ended_at = timezone.now()
            shift.save(update_fields=["is_active", "ended_at"])
            messages.info(request, f"Ended duty shift for {shift.venue.name}.")
            return redirect("staff:duty")

    channels = ContactChannel.objects.filter(staff=request.user).order_by("-is_primary", "channel_type")
    active_shifts = (
        DutyShift.objects.filter(is_active=True, ended_at__isnull=True)
        .select_related("venue", "staff", "contact_channel")
        .order_by("-started_at")
    )
    primary_venue = Venue.objects.filter(is_active=True).first()
    active_shift, active_channel = get_active_concierge(primary_venue)
    sample_deeplink = build_concierge_deeplink(active_channel, venue=primary_venue)

    return render(
        request,
        "staff/duty.html",
        {
            "my_account": my_account,
            "is_approved_staff": approved,
            "channel_form": channel_form,
            "shift_form": shift_form,
            "channels": channels,
            "active_shifts": active_shifts,
            "active_shift": active_shift,
            "active_channel": active_channel,
            "sample_deeplink": sample_deeplink,
        },
    )
