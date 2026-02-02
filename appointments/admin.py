from django.contrib import admin

# Register your models here.
# appointments/admin.py

from .models import Appointment

admin.site.register(Appointment)