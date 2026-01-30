from django.db import models
from patients.models import Patient
from accounts.models import User

class Bill(models.Model):
    """Billing model"""
    BILL_TYPE_CHOICES = (
        ('consultation', 'Consultation'),
        ('treatment', 'Treatment'),
        ('medicine', 'Medicine'),
        ('test', 'Laboratory Test'),
        ('procedure', 'Procedure'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('cancelled', 'Cancelled'),
    )
    
    bill_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bills')
    bill_type = models.CharField(max_length=20, choices=BILL_TYPE_CHOICES)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.bill_number} - {self.patient.patient_id}"
    
    def save(self, *args, **kwargs):
        self.total_amount = self.amount - self.discount
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']


class Payment(models.Model):
    """Payment model with Paystack integration"""
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('paystack', 'Paystack Online'),
        ('bank_transfer', 'Bank Transfer'),
        ('insurance', 'Insurance'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payments')
    payment_reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Payment {self.payment_reference} - {self.bill.bill_number}"
    
    class Meta:
        ordering = ['-transaction_date']