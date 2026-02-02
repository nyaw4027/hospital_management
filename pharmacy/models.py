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


class Medication(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100) # Antibiotics, Painkillers, etc.
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10) # Alert when below this
    expiry_date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.current_stock} left)"

    @property
    def is_low_stock(self):
        return self.current_stock <= self.reorder_level


class DispensingLog(models.Model):
    pharmacist = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    patient_name = models.CharField(max_length=255)
    medication_name = models.CharField(max_length=255)
    quantity_dispensed = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.medication_name} dispensed to {self.patient_name} by {self.pharmacist}"




