from urllib.parse import quote

from .models import ContactChannel, DutyShift, StaffAccount


def get_or_create_staff_account(user):
    """Ensure an authenticated user has a corresponding StaffAccount record."""
    if not user or not user.is_authenticated:
        return None
    default_role = "SUPER_ADMIN" if user.is_superuser else "STAFF"
    default_status = "APPROVED" if user.is_superuser else "PENDING"
    account, _ = StaffAccount.objects.get_or_create(
        user=user,
        defaults={
            "role": default_role,
            "verification_status": default_status,
        },
    )
    if user.is_superuser and (account.role != "SUPER_ADMIN" or account.verification_status != "APPROVED"):
        account.role = "SUPER_ADMIN"
        account.verification_status = "APPROVED"
        account.save(update_fields=["role", "verification_status"])
    return account


def is_approved_staff(user):
    """Return True if the user is verified to perform floor/reservation mutations."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    account = get_or_create_staff_account(user)
    return bool(account and account.verification_status == "APPROVED")


def is_super_admin(user):
    """Return True if the user is an approved Super Admin."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    account = get_or_create_staff_account(user)
    return bool(
        account
        and account.verification_status == "APPROVED"
        and account.role == "SUPER_ADMIN"
    )


def get_active_concierge(venue):
    """Return (active_shift, active_channel) for a venue, or (None, None)."""
    if not venue:
        return None, None
    shift = (
        DutyShift.objects.filter(venue=venue, is_active=True, ended_at__isnull=True)
        .select_related("staff", "contact_channel")
        .order_by("-started_at")
        .first()
    )
    if not shift:
        return None, None
    channel = shift.contact_channel
    if not channel or not channel.is_active:
        channel = (
            ContactChannel.objects.filter(staff=shift.staff, is_active=True)
            .order_by("-is_primary", "id")
            .first()
        )
    return shift, channel


def build_concierge_deeplink(channel, venue=None, table=None):
    """Build a direct One-Tap Connect URL with pre-filled table context."""
    venue_name = venue.name if venue else "FloorSync Venue"
    if table:
        msg = (
            f"Hi! I'd like to inquire about reserving Table {table.code}"
            f" ({table.zone.name}, {table.capacity} pax, ₱{table.min_spend:,.2f} min spend)"
            f" at {venue_name}."
        )
    else:
        msg = f"Hi! I'd like to inquire about table availability at {venue_name}."
    encoded_msg = quote(msg)

    if channel:
        raw = channel.handle_or_url.strip()
        ctype = channel.channel_type
        if raw.startswith(("http://", "https://", "tel:", "sms:", "viber://")):
            if "wa.me/" in raw and "?text=" not in raw:
                return f"{raw}?text={encoded_msg}"
            return raw
        digits = "".join(ch for ch in raw if ch.isdigit() or ch == "+")
        if ctype == "WHATSAPP":
            clean_digits = digits.lstrip("+") or raw
            return f"https://wa.me/{clean_digits}?text={encoded_msg}"
        if ctype == "MESSENGER":
            handle = raw.lstrip("@").strip("/")
            return f"https://m.me/{handle}?text={encoded_msg}"
        if ctype == "VIBER":
            return f"viber://chat?number={ quote(digits or raw) }"
        if ctype == "SMS":
            return f"sms:{digits or raw}?body={encoded_msg}"
        if ctype == "CALL":
            return f"tel:{digits or raw}"

    hotline = (venue.hotline.strip() if venue and venue.hotline else "+639170000000")
    return f"tel:{hotline}"
