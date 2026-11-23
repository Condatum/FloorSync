from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.reservations.models import TableStatusLog
from apps.staff.models import ContactChannel, DutyShift, StaffAccount

from .models import FloorPlan, Perk, Table, Venue, Zone
from .seed import seed_nocturnal_cebu


class VenueFloorMapTests(TestCase):
    def setUp(self):
        self.super_user = User.objects.create_user(
            username="super_admin", email="super@floorsync.club", password="StrongPassword123!"
        )
        StaffAccount.objects.create(
            user=self.super_user, role="SUPER_ADMIN", verification_status="APPROVED"
        )
        self.approved_staff = User.objects.create_user(
            username="floor_host", email="host@floorsync.club", password="StrongPassword123!"
        )
        StaffAccount.objects.create(
            user=self.approved_staff, role="STAFF", verification_status="APPROVED"
        )
        self.pending_staff = User.objects.create_user(
            username="pending_staff", email="pending@floorsync.club", password="StrongPassword123!"
        )
        StaffAccount.objects.create(
            user=self.pending_staff, role="STAFF", verification_status="PENDING"
        )

    def test_seed_is_idempotent_and_management_command_works(self):
        fp1 = seed_nocturnal_cebu()
        fp2 = seed_nocturnal_cebu()
        call_command("seed_venue")
        self.assertEqual(fp1.id, fp2.id)
        self.assertEqual(Venue.objects.filter(name="Nocturnal Cebu").count(), 1)
        self.assertEqual(FloorPlan.objects.filter(is_published=True).count(), 1)
        self.assertEqual(Zone.objects.filter(floor_plan=fp1).count(), 2)
        self.assertEqual(Perk.objects.count(), 4)
        self.assertEqual(Table.objects.filter(zone__floor_plan=fp1).count(), 10)

    def test_public_map_autoseeds_and_builds_concierge_deeplinks(self):
        self.assertEqual(FloorPlan.objects.filter(is_published=True).count(), 0)
        response = self.client.get(reverse("venue:public_map"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FloorPlan.objects.filter(is_published=True).count(), 1)
        self.assertContains(response, "Nocturnal Cebu")
        self.assertContains(response, 'id="table-detail-dialog"')
        self.assertContains(response, 'closedby="any"')
        self.assertContains(response, 'id="filter-zone"')
        self.assertContains(response, 'id="filter-status"')
        self.assertContains(response, 'id="filter-capacity"')
        self.assertContains(response, reverse("venue:status_api"))
        self.assertContains(response, "tel:+639178889999")

        venue = Venue.objects.get(name="Nocturnal Cebu")
        channel = ContactChannel.objects.create(
            staff=self.approved_staff,
            channel_type="WHATSAPP",
            handle_or_url="+639171112222",
            is_primary=True,
            is_active=True,
        )
        DutyShift.objects.create(
            staff=self.approved_staff,
            venue=venue,
            contact_channel=channel,
            is_active=True,
        )
        response_with_duty = self.client.get(reverse("venue:public_map"))
        self.assertEqual(response_with_duty.status_code, 200)
        self.assertContains(response_with_duty, "https://wa.me/639171112222?text=")

    def test_status_api_returns_live_counts_tables_and_concierge(self):
        floor_plan = seed_nocturnal_cebu()
        vip_table = Table.objects.get(zone__floor_plan=floor_plan, code="VIP-01")
        vip_table.status = "OCCUPIED"
        vip_table.notes = "Near main sound booth"
        vip_table.save(update_fields=["status", "notes"])

        resp = self.client.get(reverse("venue:status_api"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Cache-Control"], "no-store")
        data = resp.json()
        self.assertEqual(data["venue"]["name"], "Nocturnal Cebu")
        self.assertEqual(data["counts"]["total"], 10)
        self.assertGreaterEqual(data["counts"]["occupied"], 1)
        self.assertEqual(len(data["zones"]), 2)

        vip_payload = next(t for t in data["tables"] if t["code"] == "VIP-01")
        self.assertEqual(vip_payload["status"], "OCCUPIED")
        self.assertEqual(vip_payload["notes"], "Near main sound booth")
        self.assertIn("tel:", vip_payload["deeplink"])

    def test_admin_hub_gatekeeper_and_single_tap_toggle_creates_log(self):
        floor_plan = seed_nocturnal_cebu()
        table = Table.objects.filter(zone__floor_plan=floor_plan, code="VIP-01").first()
        original_status = table.status

        # Unauthenticated redirects to login
        anon_resp = self.client.get(reverse("venue:admin_hub"))
        self.assertEqual(anon_resp.status_code, 302)

        # Pending staff cannot mutate table status
        self.client.login(username="pending_staff", password="StrongPassword123!")
        pending_get = self.client.get(reverse("venue:admin_hub"))
        self.assertContains(pending_get, "Gatekeeper Lock")
        self.client.post(
            reverse("venue:admin_hub"),
            {"table_id": table.id, "status": "OCCUPIED"},
        )
        table.refresh_from_db()
        self.assertEqual(table.status, original_status)
        self.assertEqual(TableStatusLog.objects.count(), 0)

        # Approved staff can single-tap toggle status and record TableStatusLog
        self.client.login(username="floor_host", password="StrongPassword123!")
        self.client.post(
            reverse("venue:admin_hub"),
            {"table_id": table.id, "status": "RESERVED"},
        )
        table.refresh_from_db()
        self.assertEqual(table.status, "RESERVED")
        self.assertEqual(table.status_updated_by, self.approved_staff)
        self.assertIsNotNone(table.status_updated_at)

        log = TableStatusLog.objects.get(table=table)
        self.assertEqual(log.previous_status, original_status)
        self.assertEqual(log.new_status, "RESERVED")
        self.assertEqual(log.changed_by, self.approved_staff)
        self.assertEqual(log.source, "ADMIN_HUB")

    def test_admin_hub_filters_and_status_note_persistence(self):
        floor_plan = seed_nocturnal_cebu()
        vip_zone = Zone.objects.get(floor_plan=floor_plan, name="VIP Deck")
        vip_table = Table.objects.get(zone=vip_zone, code="VIP-01")
        self.client.login(username="floor_host", password="StrongPassword123!")

        # Submit a status toggle with an operational audit note while filtering by zone
        resp = self.client.post(
            reverse("venue:admin_hub"),
            {
                "table_id": vip_table.id,
                "status": "OCCUPIED",
                "note": "Walk-in VIP group of 8",
                "zone": str(vip_zone.id),
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(f"zone={vip_zone.id}", resp["Location"])

        log = TableStatusLog.objects.get(table=vip_table, new_status="OCCUPIED")
        self.assertEqual(log.note, "Walk-in VIP group of 8")

        # Filter by zone + status + query and verify matching table & note display
        filtered = self.client.get(
            reverse("venue:admin_hub"),
            {"zone": str(vip_zone.id), "status": "OCCUPIED", "q": "VIP-01"},
        )
        self.assertEqual(filtered.status_code, 200)
        self.assertContains(filtered, "VIP-01")
        self.assertContains(filtered, "Walk-in VIP group of 8")
        self.assertNotContains(filtered, "REG-01")

    def test_spatial_manage_super_admin_access_control(self):
        floor_plan = seed_nocturnal_cebu()
        vip_zone = Zone.objects.get(floor_plan=floor_plan, name="VIP Deck")
        perk = Perk.objects.get(name="Bottle Service")

        # Approved regular staff cannot create or edit tables
        self.client.login(username="floor_host", password="StrongPassword123!")
        staff_get = self.client.get(reverse("venue:spatial_manage"))
        self.assertContains(staff_get, "Super Admin Only")
        self.client.post(
            reverse("venue:spatial_manage"),
            {
                "zone": vip_zone.id,
                "code": "VIP-99",
                "label": "Blocked Attempt",
                "capacity": 8,
                "min_spend": "15000.00",
                "shape": "RECT",
                "pos_x": "300",
                "pos_y": "300",
                "width": "120",
                "height": "80",
                "status": "AVAILABLE",
                "is_visible": "on",
            },
        )
        self.assertFalse(Table.objects.filter(code="VIP-99").exists())

        # Super Admin can create and update tables
        self.client.login(username="super_admin", password="StrongPassword123!")
        self.client.post(
            reverse("venue:spatial_manage"),
            {
                "zone": vip_zone.id,
                "code": "VIP-06",
                "label": "Skyline Booth",
                "capacity": 10,
                "min_spend": "22000.00",
                "shape": "BOOTH",
                "pos_x": "280",
                "pos_y": "40",
                "width": "140",
                "height": "85",
                "status": "AVAILABLE",
                "is_visible": "on",
                "perks": [perk.id],
            },
        )
        created = Table.objects.get(zone=vip_zone, code="VIP-06")
        self.assertEqual(created.capacity, 10)
        self.assertEqual(created.pos_x, Decimal("280.00"))
        self.assertIn(perk, created.perks.all())

        # Update existing table
        self.client.post(
            reverse("venue:spatial_manage"),
            {
                "table_id": created.id,
                "zone": vip_zone.id,
                "code": "VIP-06",
                "label": "Skyline Booth Updated",
                "capacity": 12,
                "min_spend": "26000.00",
                "shape": "BOOTH",
                "pos_x": "295",
                "pos_y": "45",
                "width": "150",
                "height": "90",
                "status": "RESERVED",
                "perks": [perk.id],
            },
        )
        created.refresh_from_db()
        self.assertEqual(created.capacity, 12)
        self.assertFalse(created.is_visible)
        self.assertEqual(created.pos_x, Decimal("295.00"))
        self.assertTrue(
            TableStatusLog.objects.filter(
                table=created, previous_status="AVAILABLE", new_status="RESERVED", source="LAYOUT_EDIT"
            ).exists()
        )

    def test_spatial_manage_zones_and_safe_delete(self):
        floor_plan = seed_nocturnal_cebu()
        self.client.login(username="super_admin", password="StrongPassword123!")

        # Create a new Zone
        resp = self.client.post(
            reverse("venue:spatial_manage"),
            {
                "form_action": "save_zone",
                "zone-name": "Sky Lounge",
                "zone-zone_type": "VIP",
                "zone-display_color": "#06b6d4",
                "zone-sort_order": "3",
            },
        )
        self.assertEqual(resp.status_code, 302)
        new_zone = Zone.objects.get(floor_plan=floor_plan, name="Sky Lounge")
        self.assertEqual(new_zone.display_color, "#06b6d4")

        # Create an unused table and delete it safely
        temp_table = Table.objects.create(
            zone=new_zone,
            code="SKY-01",
            capacity=6,
            pos_x=Decimal("400"),
            pos_y=Decimal("400"),
        )
        del_resp = self.client.post(
            reverse("venue:spatial_manage"),
            {"form_action": "delete_table", "table_id": temp_table.id},
        )
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(Table.objects.filter(pk=temp_table.id).exists())

        # Render page and verify interactive canvas + zone UI exist
        page = self.client.get(reverse("venue:spatial_manage"))
        self.assertContains(page, 'id="spatial-preview-canvas"')
        self.assertContains(page, "Sky Lounge")
