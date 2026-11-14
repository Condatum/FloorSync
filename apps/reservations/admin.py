from django.contrib import admin

from .models import Reservation, TableStatusLog

admin.site.register(Reservation)
admin.site.register(TableStatusLog)
