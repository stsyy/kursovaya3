from django.contrib import admin

from .models import Doctor, DoctorSpecialization, Room, Specialization

admin.site.register([Specialization, Doctor, DoctorSpecialization, Room])
