from django.db import models
from django.conf import settings

class LabRequest(models.Model):
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('emergency', 'Emergency (STAT)'),
    ]

    # --- Relationships ---
    # We add null=True so Django doesn't ask for a one-off default
    patient = models.ForeignKey(
        'patients.Patient', 
        on_delete=models.CASCADE, 
        related_name='lab_requests',
        null=True,
        blank=True
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='requested_tests'
    )
    
    test_name = models.CharField(max_length=200)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    clinical_notes = models.TextField(blank=True)
    findings = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='lab_results/%Y/%m/%d/', blank=True, null=True)
    status = models.CharField(max_length=20, default='pending') 
    is_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        patient_name = self.patient.name if self.patient else "Unknown"
        return f"{self.test_name} - {patient_name}"

class Reagent(models.Model):
    name = models.CharField(max_length=100)
    stock_quantity = models.PositiveIntegerField(default=0)
    min_threshold = models.PositiveIntegerField(default=10)
    last_restocked = models.DateTimeField(auto_now=True)
  
    def __str__(self):
        return self.name