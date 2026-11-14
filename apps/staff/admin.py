from django.contrib import admin

from .models import ContactChannel, DutyShift, StaffAccount

admin.site.register(StaffAccount)
admin.site.register(ContactChannel)
admin.site.register(DutyShift)
