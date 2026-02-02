# patients/models.py
from django.db import models
from django.conf import settings

class Patient(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')
    patient_id = models.CharField(max_length=20, unique=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True) # This is a text field, which is fine
    allergies = models.TextField(blank=True, null=True)
    is_admitted = models.BooleanField(default=False) 
    
    def __str__(self):
        return f"{self.patient_id} - {self.user.get_full_name()}"


# patients/models.py

class Vitals(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='vitals')
    temperature = models.DecimalField(max_digits=4, decimal_places=1, help_text="in Celsius")
    bp = models.CharField( max_length=20, help_text="e.g. 120/80")
    pulse = models.PositiveIntegerField(help_text="bpm")
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="kg")
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vitals for {self.patient.user.get_full_name()} at {self.recorded_at}"
