from django.contrib import admin
from .models import Patient, Appointment, MedicalRecord

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'user', 'blood_group', 'created_at']
    search_fields = ['patient_id', 'user__username', 'user__email']
    list_filter = ['blood_group', 'created_at']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'status']
    list_filter = ['status', 'appointment_date']
    search_fields = ['patient__patient_id', 'doctor__username']

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'visit_date']
    list_filter = ['visit_date']
    search_fields = ['patient__patient_id', 'doctor__username']