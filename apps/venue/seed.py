from decimal import Decimal

from django.db import transaction

from .models import FloorPlan, Perk, Table, TablePerk, Venue, Zone

NOCTURNAL_CEBU_TABLES = [
    {
        "zone": "VIP Deck",
        "code": "VIP-01",
        "label": "Royal Booth 1",
        "capacity": 10,
        "min_spend": Decimal("25000.00"),
        "shape": "BOOTH",
        "pos_x": Decimal("70.00"),
        "pos_y": Decimal("40.00"),
        "width": Decimal("160.00"),
        "height": Decimal("90.00"),
        "status": "AVAILABLE",
        "perks": ["Near DJ Booth", "Bottle Service", "Private Booth"],
    },
    {
        "zone": "VIP Deck",
        "code": "VIP-02",
        "label": "Royal Booth 2",
        "capacity": 10,
        "min_spend": Decimal("25000.00"),
        "shape": "BOOTH",
        "pos_x": Decimal("970.00"),
        "pos_y": Decimal("40.00"),
        "width": Decimal("160.00"),
        "height": Decimal("90.00"),
        "status": "RESERVED",
        "perks": ["Near DJ Booth", "Bottle Service", "Private Booth"],
    },
    {
        "zone": "VIP Deck",
        "code": "VIP-03",
        "label": "Deck Lounge A",
        "capacity": 8,
        "min_spend": Decimal("18000.00"),
        "shape": "RECT",
        "pos_x": Decimal("70.00"),
        "pos_y": Decimal("175.00"),
        "width": Decimal("150.00"),
        "height": Decimal("85.00"),
        "status": "OCCUPIED",
        "perks": ["Near DJ Booth", "Dance Floor View", "Bottle Service"],
    },
    {
        "zone": "VIP Deck",
        "code": "VIP-04",
        "label": "Deck Lounge B",
        "capacity": 8,
        "min_spend": Decimal("18000.00"),
        "shape": "RECT",
        "pos_x": Decimal("980.00"),
        "pos_y": Decimal("175.00"),
        "width": Decimal("150.00"),
        "height": Decimal("85.00"),
        "status": "AVAILABLE",
        "perks": ["Near DJ Booth", "Dance Floor View", "Bottle Service"],
    },
    {
        "zone": "VIP Deck",
        "code": "VIP-05",
        "label": "Center Stage VIP",
        "capacity": 12,
        "min_spend": Decimal("35000.00"),
        "shape": "BOOTH",
        "pos_x": Decimal("480.00"),
        "pos_y": Decimal("135.00"),
        "width": Decimal("240.00"),
        "height": Decimal("85.00"),
        "status": "AVAILABLE",
        "perks": ["Near DJ Booth", "Dance Floor View", "Bottle Service", "Private Booth"],
    },
    {
        "zone": "Regular Floor",
        "code": "REG-01",
        "label": "Floor Circle 1",
        "capacity": 4,
        "min_spend": Decimal("5000.00"),
        "shape": "CIRCLE",
        "pos_x": Decimal("100.00"),
        "pos_y": Decimal("355.00"),
        "width": Decimal("95.00"),
        "height": Decimal("95.00"),
        "status": "AVAILABLE",
        "perks": ["Dance Floor View"],
    },
    {
        "zone": "Regular Floor",
        "code": "REG-02",
        "label": "Floor Circle 2",
        "capacity": 4,
        "min_spend": Decimal("5000.00"),
        "shape": "CIRCLE",
        "pos_x": Decimal("1005.00"),
        "pos_y": Decimal("355.00"),
        "width": Decimal("95.00"),
        "height": Decimal("95.00"),
        "status": "OCCUPIED",
        "perks": ["Dance Floor View"],
    },
    {
        "zone": "Regular Floor",
        "code": "REG-03",
        "label": "Main High-Top 1",
        "capacity": 6,
        "min_spend": Decimal("7500.00"),
        "shape": "RECT",
        "pos_x": Decimal("110.00"),
        "pos_y": Decimal("590.00"),
        "width": Decimal("140.00"),
        "height": Decimal("85.00"),
        "status": "AVAILABLE",
        "perks": ["Dance Floor View"],
    },
    {
        "zone": "Regular Floor",
        "code": "REG-04",
        "label": "Main High-Top 2",
        "capacity": 6,
        "min_spend": Decimal("7500.00"),
        "shape": "RECT",
        "pos_x": Decimal("530.00"),
        "pos_y": Decimal("610.00"),
        "width": Decimal("140.00"),
        "height": Decimal("85.00"),
        "status": "RESERVED",
        "perks": ["Dance Floor View", "Bottle Service"],
    },
    {
        "zone": "Regular Floor",
        "code": "REG-05",
        "label": "Corner Lounge",
        "capacity": 6,
        "min_spend": Decimal("6000.00"),
        "shape": "RECT",
        "pos_x": Decimal("950.00"),
        "pos_y": Decimal("590.00"),
        "width": Decimal("140.00"),
        "height": Decimal("85.00"),
        "status": "BLOCKED",
        "perks": ["Private Booth"],
    },
]

PERK_DEFINITIONS = [
    ("Near DJ Booth", "headphones", "Direct sightline and proximity to the DJ console."),
    ("Dance Floor View", "sparkles", "Unobstructed view of the main dance floor."),
    ("Bottle Service", "wine", "Dedicated VIP host and bottle presentation service."),
    ("Private Booth", "shield", "Semi-enclosed seating with dedicated booth privacy."),
]


@transaction.atomic
def seed_nocturnal_cebu(created_by=None):
    """Idempotently seed Nocturnal Cebu venue, Main Floor plan, zones, perks, and 10 tables."""
    venue, _ = Venue.objects.get_or_create(
        name="Nocturnal Cebu",
        defaults={
            "address": "IT Park, Cebu City",
            "hotline": "+639178889999",
            "is_active": True,
        },
    )
    if venue.hotline != "+639178889999":
        venue.hotline = "+639178889999"
        venue.save(update_fields=["hotline"])

    floor_plan, created_fp = FloorPlan.objects.get_or_create(
        venue=venue,
        name="Main Floor",
        version=1,
        defaults={
            "canvas_width": 1200,
            "canvas_height": 800,
            "is_published": True,
            "created_by": created_by,
        },
    )
    if not created_fp and not floor_plan.is_published:
        floor_plan.is_published = True
        floor_plan.save(update_fields=["is_published"])

    vip_zone, _ = Zone.objects.get_or_create(
        floor_plan=floor_plan,
        name="VIP Deck",
        defaults={
            "zone_type": "VIP",
            "display_color": "#8b5cf6",
            "sort_order": 1,
        },
    )
    regular_zone, _ = Zone.objects.get_or_create(
        floor_plan=floor_plan,
        name="Regular Floor",
        defaults={
            "zone_type": "REGULAR",
            "display_color": "#06b6d4",
            "sort_order": 2,
        },
    )
    zone_map = {
        "VIP Deck": vip_zone,
        "Regular Floor": regular_zone,
    }

    perk_map = {}
    for perk_name, icon, description in PERK_DEFINITIONS:
        perk, _ = Perk.objects.get_or_create(
            name=perk_name,
            defaults={"icon": icon, "description": description},
        )
        perk_map[perk_name] = perk

    for spec in NOCTURNAL_CEBU_TABLES:
        zone = zone_map[spec["zone"]]
        table, _ = Table.objects.get_or_create(
            zone=zone,
            code=spec["code"],
            defaults={
                "label": spec["label"],
                "capacity": spec["capacity"],
                "min_spend": spec["min_spend"],
                "shape": spec["shape"],
                "pos_x": spec["pos_x"],
                "pos_y": spec["pos_y"],
                "width": spec["width"],
                "height": spec["height"],
                "status": spec["status"],
                "is_visible": True,
            },
        )
        for perk_name in spec["perks"]:
            TablePerk.objects.get_or_create(table=table, perk=perk_map[perk_name])

    return floor_plan
