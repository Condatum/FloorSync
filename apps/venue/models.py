from django.contrib.auth.models import User
from django.db import models


class Venue(models.Model):
    name = models.CharField(max_length=120, unique=True)
    address = models.CharField(max_length=255, blank=True)
    hotline = models.CharField(max_length=20, blank=True)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FloorPlan(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="floor_plans")
    name = models.CharField(max_length=120)
    version = models.PositiveIntegerField(default=1)
    background_image = models.ImageField(upload_to="floorplans/", null=True, blank=True)
    canvas_width = models.PositiveIntegerField(default=1200)
    canvas_height = models.PositiveIntegerField(default=800)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="floor_plans")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("venue", "name", "version")

    def __str__(self):
        return f"{self.name} v{self.version}"


class Zone(models.Model):
    ZONE_TYPES = [("VIP", "VIP"), ("REGULAR", "Regular")]

    floor_plan = models.ForeignKey(FloorPlan, on_delete=models.CASCADE, related_name="zones")
    name = models.CharField(max_length=80)
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPES)
    display_color = models.CharField(max_length=7, default="#7C3AED")
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ("floor_plan", "name")

    def __str__(self):
        return self.name


class Perk(models.Model):
    name = models.CharField(max_length=60, unique=True)
    icon = models.CharField(max_length=40, blank=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Table(models.Model):
    SHAPES = [("RECT", "Rectangle"), ("CIRCLE", "Circle"), ("BOOTH", "Booth")]
    STATUSES = [("AVAILABLE", "Available"), ("OCCUPIED", "Occupied"),
                ("RESERVED", "Reserved"), ("BLOCKED", "Blocked")]

    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="tables")
    code = models.CharField(max_length=20)
    label = models.CharField(max_length=60, blank=True)
    capacity = models.SmallIntegerField()
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shape = models.CharField(max_length=15, choices=SHAPES, default="RECT")
    pos_x = models.DecimalField(max_digits=7, decimal_places=2)
    pos_y = models.DecimalField(max_digits=7, decimal_places=2)
    width = models.DecimalField(max_digits=7, decimal_places=2, default=80)
    height = models.DecimalField(max_digits=7, decimal_places=2, default=60)
    rotation = models.SmallIntegerField(default=0)
    status = models.CharField(max_length=15, choices=STATUSES, default="AVAILABLE")
    status_updated_at = models.DateTimeField(null=True, blank=True)
    status_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name="tables_updated")
    is_visible = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)
    perks = models.ManyToManyField(Perk, through="TablePerk", related_name="tables")

    class Meta:
        unique_together = ("zone", "code")

    def __str__(self):
        return self.code


class TablePerk(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    perk = models.ForeignKey(Perk, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("table", "perk")

    def __str__(self):
        return f"{self.table} / {self.perk}"
