from django.db import models
from django.conf import settings

# Use string references to avoid circular imports
# 'patients.Patient' points to Patient model in patients app
# 'accounts.User' points to User model in accounts app

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
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='bills'
    )
    bill_type = models.CharField(max_length=20, choices=BILL_TYPE_CHOICES)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_bills'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.bill_number} - {self.patient.patient_id}"
    
    def save(self, *args, **kwargs):
        # Automatically calculate total_amount
        self.total_amount = self.amount - self.discount
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']


class Payment(models.Model):
    """Integrated Payment model for General Bills and Lab Requests"""
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
    
    # Links
    patient = models.ForeignKey(
        'patients.Patient', 
        on_delete=models.CASCADE, 
        related_name='payments',
        null=True,   # Add this
        blank=True   # Add this

    )
    
    # A payment can belong to a General Bill OR a specific Lab Request
    bill = models.ForeignKey(
        'cashier.Bill',
        on_delete=models.CASCADE,
        related_name='payments',
        null=True, # Set to True to allow Lab-only payments
        blank=True
    )
    
    lab_request = models.ForeignKey(
        'labs.LabRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )

    # Transaction Details
    payment_reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments_processed'
    )
    
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        if self.lab_request:
            return f"Lab Payment {self.payment_reference} - {self.lab_request.test_name}"
        return f"Bill Payment {self.payment_reference} - {self.bill.bill_number if self.bill else 'N/A'}"
    
    class Meta:
        ordering = ['-transaction_date']




class Invoice(models.Model):
    STATUS_CHOICES = [
        ('unpaid', 'Unpaid'), 
        ('paid', 'Paid'), 
        ('partially_paid', 'Partially Paid')
    ]
    
    # We use strings 'app_label.ModelName' to avoid NameErrors
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Paperless links using strings
    prescriptions = models.ManyToManyField('doctors.Prescription', blank=True)
    lab_requests = models.ManyToManyField('doctors.LabRequest', blank=True)

    def __str__(self):
        # self.patient.user.get_full_name() will work once the apps are loaded
        return f"Invoice {self.id} - {self.patient}"