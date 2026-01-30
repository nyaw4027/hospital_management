from django.db import models
from accounts.models import User

class Patient(models.Model):
    """Patient model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    patient_id = models.CharField(max_length=20, unique=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Height in cm")
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    medical_history = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient_id} - {self.user.get_full_name()}"
    
    class Meta:
        ordering = ['-created_at']


class Appointment(models.Model):
    """Appointment model"""
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments', limit_choices_to={'role': 'doctor'})
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient.patient_id} - {self.doctor.get_full_name()} on {self.appointment_date}"
    
    class Meta:
        ordering = ['-appointment_date', '-appointment_time']


class MedicalRecord(models.Model):
    """Medical Record model"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_records')
    diagnosis = models.TextField()
    prescription = models.TextField()
    test_results = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    visit_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Record for {self.patient.patient_id} by {self.doctor.get_full_name()}"
    
    class Meta:
        ordering = ['-visit_date']