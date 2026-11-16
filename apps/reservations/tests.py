from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.staff.models import StaffAccount
from apps.venue.models import Table
from apps.venue.seed import seed_nocturnal_cebu

from .models import Reservation, TableStatusLog


class ReservationsAndAuditTests(TestCase):
    def setUp(self):
        self.floor_plan = seed_nocturnal_cebu()
        self.table = Table.objects.filter(zone__floor_plan=self.floor_plan, code="VIP-01").first()

        self.approved_staff = User.objects.create_user(
            username="floor_host",
            email="host@floorsync.club",
            password="StrongPassword123!",
        )
        StaffAccount.objects.create(
            user=self.approved_staff,
            role="STAFF",
            verification_status="APPROVED",
        )

        self.pending_staff = User.objects.create_user(
            username="pending_host",
            email="pending@floorsync.club",
            password="StrongPassword123!",
        )
        StaffAccount.objects.create(
            user=self.pending_staff,
            role="STAFF",
            verification_status="PENDING",
        )

    def test_gatekeeper_blocks_unapproved_staff_from_creating_reservations(self):
        anon_resp = self.client.get(reverse("reservations:list"))
        self.assertEqual(anon_resp.status_code, 302)

        self.client.login(username="pending_host", password="StrongPassword123!")
        get_resp = self.client.get(reverse("reservations:list"))
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, "Gatekeeper Lock")

        post_resp = self.client.post(
            reverse("reservations:list"),
            {
                "action": "create",
                "table": self.table.id,
                "guest_name": "Unauthorized Guest",
                "guest_contact": "+639170001111",
                "party_size": 4,
                "reserved_for": "2026-11-20T22:00",
                "deposit_amount": "5000.00",
                "payment_verified": "on",
                "status": "CONFIRMED",
                "remarks": "Should be blocked",
            },
        )
        self.assertEqual(post_resp.status_code, 302)
        self.assertEqual(Reservation.objects.count(), 0)
        self.assertEqual(TableStatusLog.objects.count(), 0)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, "AVAILABLE")

    def test_approved_staff_creates_verified_reservation_syncs_table_and_writes_log(self):
        self.client.login(username="floor_host", password="StrongPassword123!")

        post_resp = self.client.post(
            reverse("reservations:list"),
            {
                "action": "create",
                "table": self.table.id,
                "guest_name": "Marco Reyes",
                "guest_contact": "+639171234567",
                "party_size": 6,
                "reserved_for": "2026-11-20T22:30",
                "deposit_amount": "10000.00",
                "payment_verified": "on",
                "status": "CONFIRMED",
                "remarks": "Dom Perignon bottle ready",
            },
        )
        self.assertEqual(post_resp.status_code, 302)
        self.assertEqual(Reservation.objects.count(), 1)

        res = Reservation.objects.first()
        self.assertTrue(res.reference_code.startswith("FS-"))
        self.assertEqual(len(res.reference_code), 9)
        self.assertEqual(res.guest_name, "Marco Reyes")
        self.assertEqual(res.deposit_amount, Decimal("10000.00"))
        self.assertTrue(res.payment_verified)
        self.assertEqual(res.status, "CONFIRMED")
        self.assertEqual(res.created_by, self.approved_staff)

        self.table.refresh_from_db()
        self.assertEqual(self.table.status, "RESERVED")
        self.assertEqual(self.table.status_updated_by, self.approved_staff)

        log = TableStatusLog.objects.get(reservation=res)
        self.assertEqual(log.table, self.table)
        self.assertEqual(log.source, "ADMIN_HUB")
        self.assertEqual(log.previous_status, "AVAILABLE")
        self.assertEqual(log.new_status, "RESERVED")
        self.assertEqual(log.changed_by, self.approved_staff)

        # Updating reservation to SEATED syncs table to OCCUPIED and logs again
        update_resp = self.client.post(
            reverse("reservations:list"),
            {
                "action": "update",
                "reservation_id": res.id,
                "status": "SEATED",
                "payment_verified": "on",
            },
        )
        self.assertEqual(update_resp.status_code, 302)
        self.table.refresh_from_db()
        self.assertEqual(self.table.status, "OCCUPIED")
        self.assertEqual(TableStatusLog.objects.filter(reservation=res).count(), 2)

    def test_audit_log_view_renders_table_status_logs(self):
        self.client.login(username="floor_host", password="StrongPassword123!")
        self.client.post(
            reverse("reservations:list"),
            {
                "action": "create",
                "table": self.table.id,
                "guest_name": "Elena Cruz",
                "guest_contact": "@elenacruz",
                "party_size": 4,
                "reserved_for": "2026-11-21T23:00",
                "deposit_amount": "8000.00",
                "payment_verified": "on",
                "status": "HELD",
                "remarks": "",
            },
        )
        res = Reservation.objects.get(guest_name="Elena Cruz")

        audit_resp = self.client.get(reverse("reservations:audit"))
        self.assertEqual(audit_resp.status_code, 200)
        self.assertContains(audit_resp, "VIP-01")
        self.assertContains(audit_resp, "AVAILABLE")
        self.assertContains(audit_resp, "RESERVED")
        self.assertContains(audit_resp, res.reference_code)
        self.assertContains(audit_resp, "Admin Hub")
        self.assertContains(audit_resp, "floor_host")
