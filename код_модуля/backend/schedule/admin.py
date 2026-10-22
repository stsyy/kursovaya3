from django.contrib import admin

from .models import Shift, Slot, UnavailabilityPeriod

admin.site.register([Shift, Slot, UnavailabilityPeriod])
