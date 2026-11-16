from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.venue.models import Venue

from .models import ContactChannel, DutyShift, StaffAccount
from .utils import build_concierge_deeplink, get_active_concierge, is_approved_staff, is_super_admin


class StaffGatekeeperAndDutyTests(TestCase):
    def setUp(self):
        self.super_user = User.objects.create_user(
            username="super_boss", email="boss@floorsync.club", password="StrongPassword123!"
        )
        StaffAccount.objects.create(
            user=self.super_user, role="SUPER_ADMIN", verification_status="APPROVED"
        )
        self.pending_user = User.objects.create_user(
            username="new_bouncer", email="bouncer@floorsync.club", password="StrongPassword123!"
        )
        self.pending_account = StaffAccount.objects.create(
            user=self.pending_user, role="STAFF", verification_status="PENDING"
        )
        self.venue = Venue.objects.create(name="Nocturnal Cebu", hotline="+639178889999")

    def test_gatekeeper_permissions_and_super_admin_approval(self):
        self.assertTrue(is_super_admin(self.super_user))
        self.assertFalse(is_approved_staff(self.pending_user))

        self.client.login(username="super_boss", password="StrongPassword123!")
        response = self.client.post(
            reverse("staff:vetting"),
            {"account_id": self.pending_account.id, "action": "approve"},
        )
        self.assertRedirects(response, reverse("staff:vetting"))
        self.pending_account.refresh_from_db()
        self.assertEqual(self.pending_account.verification_status, "APPROVED")
        self.assertTrue(is_approved_staff(self.pending_user))

    def test_duty_shift_and_concierge_deeplink_routing(self):
        self.client.login(username="super_boss", password="StrongPassword123!")
        self.client.post(
            reverse("staff:duty"),
            {
                "form_type": "add_channel",
                "channel-channel_type": "WHATSAPP",
                "channel-handle_or_url": "+639171234567",
                "channel-is_primary": "on",
                "channel-is_active": "on",
            },
        )
        channel = ContactChannel.objects.get(staff=self.super_user, channel_type="WHATSAPP")
        self.client.post(
            reverse("staff:duty"),
            {
                "form_type": "start_shift",
                "shift-venue": self.venue.id,
                "shift-contact_channel": channel.id,
            },
        )
        active_shift, active_channel = get_active_concierge(self.venue)
        self.assertIsNotNone(active_shift)
        self.assertEqual(active_channel, channel)
        deeplink = build_concierge_deeplink(active_channel, venue=self.venue)
        self.assertIn("https://wa.me/639171234567?text=", deeplink)
        self.assertEqual(DutyShift.objects.filter(venue=self.venue, is_active=True).count(), 1)
