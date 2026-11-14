from django.contrib.auth.models import User
from django.db import models


class StaffAccount(models.Model):
    ROLES = [("SUPER_ADMIN", "Super Admin"), ("STAFF", "Staff")]
    STATUSES = [("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff_account")
    role = models.CharField(max_length=20, choices=ROLES, default="STAFF")
    verification_status = models.CharField(max_length=20, choices=STATUSES, default="PENDING")
    employee_no = models.CharField(max_length=20, unique=True, null=True, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="verified_staff_accounts")
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class ContactChannel(models.Model):
    CHANNELS = [("MESSENGER", "Messenger"), ("VIBER", "Viber"), ("WHATSAPP", "WhatsApp"),
                ("SMS", "SMS"), ("CALL", "Call")]

    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contact_channels")
    channel_type = models.CharField(max_length=20, choices=CHANNELS)
    handle_or_url = models.CharField(max_length=255)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("staff", "channel_type")

    def __str__(self):
        return f"{self.staff.username} / {self.channel_type}"


class DutyShift(models.Model):
    venue = models.ForeignKey("venue.Venue", on_delete=models.CASCADE, related_name="duty_shifts")
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name="duty_shifts")
    contact_channel = models.ForeignKey(ContactChannel, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name="duty_shifts")
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.staff.username} @ {self.venue}"
