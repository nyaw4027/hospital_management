from django.db import models
from django.conf import settings

# --- 1. Doctor Profile ---
class Doctor(models.Model):
    SPECIALIZATION_CHOICES = (
        ('cardiology', 'Cardiology'), ('neurology', 'Neurology'),
        ('pediatrics', 'Pediatrics'), ('orthopedics', 'Orthopedics'),
        ('dermatology', 'Dermatology'), ('general', 'General Medicine'),
        ('surgery', 'Surgery'), ('psychiatry', 'Psychiatry'),
        ('radiology', 'Radiology'), ('other', 'Other'),
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='doctor_profile'
    )
    doctor_id = models.CharField(max_length=20, unique=True)
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES)
    license_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    qualification = models.CharField(max_length=200)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} ({self.get_specialization_display()})"

# --- 2. Medical Record ---
# doctors/models.py

class MedicalRecord(models.Model):
    appointment = models.OneToOneField(
        'appointments.Appointment', 
        on_delete=models.CASCADE, 
        related_name='medical_record'
    )
    patient = models.ForeignKey(
        'patients.Patient', 
        on_delete=models.CASCADE, 
        related_name='patient_records'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    diagnosis = models.CharField(max_length=255)
    clinical_notes = models.TextField()
    
    ordered_tests = models.BooleanField(default=False)
    prescribed_medicines = models.BooleanField(default=False)
    
    # ADD THIS LINE TO FIX THE ERROR:
    requires_admission = models.BooleanField(default=False) 
    
    visit_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Record for {self.patient} - {self.visit_date.date()}"

# --- 3. Paperless Lab Requests ---
class LabRequest(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('completed', 'Completed'), ('cancelled', 'Cancelled')]
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='lab_requests')
    test_name = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    results = models.TextField(blank=True)
    lab_tech = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='processed_labs')
    recorded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Lab: {self.test_name} for {self.medical_record.patient}"

# --- 4. Professional Prescription Header ---
class Prescription(models.Model):
    STATUS_CHOICES = [('pending', 'Pending Dispensing'), ('dispensed', 'Dispensed'), ('cancelled', 'Cancelled')]

    medical_record = models.OneToOneField(MedicalRecord, on_delete=models.CASCADE, related_name='prescription_link', null=True)
    doctor_profile = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='prescriptions')
    
    diagnosis = models.TextField()
    clinical_notes = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RX#{self.id} - {self.patient}"

# --- 5. Prescription Medicine Items ---
class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, related_name='items', on_delete=models.CASCADE)
    medicine_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100) 
    frequency = models.CharField(max_length=100) 
    duration = models.CharField(max_length=100) 
    quantity = models.PositiveIntegerField(default=1)
    instructions = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.medicine_name} ({self.dosage})"