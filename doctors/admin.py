from django.contrib import admin
from .models import Doctor, MedicalRecord, LabRequest, Prescription, PrescriptionItem

# 1. Nesting Medicines inside the Prescription view
class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1 # Provides one empty row for new medicines
    fields = ('medicine_name', 'dosage', 'frequency', 'duration', 'quantity', 'instructions')

# 2. Doctor Profile Admin
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    # 'license_number' is included because we added it to our final model
    list_display = ('doctor_id', 'user', 'specialization', 'consultation_fee')
    list_filter = ('specialization',)
    search_fields = ('doctor_id', 'user__first_name', 'user__last_name')

# 3. Medical Record Admin
@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'diagnosis', 'visit_date', 'ordered_tests', 'prescribed_medicines')
    list_filter = ('visit_date', 'ordered_tests', 'prescribed_medicines')
    search_fields = ('patient__patient_id', 'diagnosis')

# 4. Lab Request Admin
@admin.register(LabRequest)
class LabRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'medical_record', 'test_name', 'status')
    list_filter = ('status',)
    search_fields = ('test_name', 'medical_record__patient__patient_id')

# 5. Prescription Admin (With Inlines)
@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor_profile', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [PrescriptionItemInline]
    search_fields = ('patient__user__last_name', 'diagnosis')

# Note: PrescriptionItem is not registered separately to keep the sidebar clean,
# since it is managed inside the Prescription Admin.