from django.db import models
from django.conf import settings
from accounts.models import Patient  # Ensure this path matches your app structure

class Ward(models.Model):
    WARD_TYPES = [('General', 'General'), ('ICU', 'ICU'), ('Maternity', 'Maternity'), ('Pediatric', 'Pediatric')]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=WARD_TYPES)
    rate_per_night = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    total_beds = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} ({self.category})"

class Admission(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE)
    bed_number = models.CharField(max_length=10)
    admitted_at = models.DateTimeField(auto_now_add=True)
    discharged_at = models.DateTimeField(null=True, blank=True)
    is_discharged = models.BooleanField(default=False)
    reason = models.TextField()

    def __str__(self):
        return f"{self.patient} - Bed {self.bed_number}"

class VitalSign(models.Model):
    """Nursing Rounds Log"""
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='vitals')
    nurse = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1) # e.g., 37.5
    blood_pressure = models.CharField(max_length=20) # e.g., 120/80
    pulse_rate = models.PositiveIntegerField()
    notes = models.TextField(blank=True)




    