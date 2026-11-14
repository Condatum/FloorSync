from django.contrib import admin

from .models import FloorPlan, Perk, Table, TablePerk, Venue, Zone

admin.site.register(Venue)
admin.site.register(FloorPlan)
admin.site.register(Zone)
admin.site.register(Table)
admin.site.register(Perk)
admin.site.register(TablePerk)
