from django.contrib import admin
from .models import Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['doctor_id', 'user', 'specialization', 'consultation_fee', 'experience_years']
    list_filter = ['specialization', 'experience_years']
    search_fields = ['doctor_id', 'user__username', 'user__email', 'license_number']