from django.contrib import admin

from .models import Doctor, Room, Specialization

admin.site.register([Specialization, Doctor, Room])
