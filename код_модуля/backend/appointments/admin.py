from django.contrib import admin

from .models import Appointment, Patient, SmsNotification

admin.site.register([Patient, Appointment, SmsNotification])
