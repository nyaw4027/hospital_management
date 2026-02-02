from django.db import models
from django.conf import settings

class Prescription(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('dispensed', 'Dispensed'),
    ]
    
    # 1. Use a string 'app_label.ModelName' to avoid the Import
    patient = models.ForeignKey('accounts.Patient', on_delete=models.CASCADE)
    
    # 2. Use settings.AUTH_USER_MODEL for the User relationship
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.medication_name} - {self.status}"