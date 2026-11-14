from django.contrib.auth.models import User
from django.db import models


class Reservation(models.Model):
    STATUSES = [("HELD", "Held"), ("CONFIRMED", "Confirmed"), ("SEATED", "Seated"),
                ("COMPLETED", "Completed"), ("CANCELLED", "Cancelled"), ("NO_SHOW", "No show")]

    table = models.ForeignKey("venue.Table", on_delete=models.PROTECT, related_name="reservations")
    reference_code = models.CharField(max_length=12, unique=True)
    guest_name = models.CharField(max_length=120)
    guest_contact = models.CharField(max_length=50)
    party_size = models.SmallIntegerField()
    reserved_for = models.DateTimeField()
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_verified = models.BooleanField(default=False)
    status = models.CharField(max_length=15, choices=STATUSES, default="HELD")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="reservations_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.reference_code} - {self.guest_name}"


class TableStatusLog(models.Model):
    SOURCES = [("ADMIN_HUB", "Admin Hub"), ("LAYOUT_EDIT", "Layout edit"), ("SYSTEM", "System")]

    table = models.ForeignKey("venue.Table", on_delete=models.CASCADE, related_name="status_logs")
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="status_logs")
    previous_status = models.CharField(max_length=15)
    new_status = models.CharField(max_length=15)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="status_changes")
    changed_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=20, choices=SOURCES, default="ADMIN_HUB")
    note = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.table}: {self.previous_status} -> {self.new_status}"
