# patients/admin.py
from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    # Only fields that exist in your Patient model
    list_display = ('patient_id', 'user', 'blood_group', 'is_admitted')
    list_filter = ('blood_group', 'is_admitted')
    search_fields = ('patient_id', 'user__first_name', 'user__last_name', 'user__email')