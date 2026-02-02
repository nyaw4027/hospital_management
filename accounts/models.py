from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('cashier', 'Cashier'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
        ('pharmacist', 'Pharmacist'), # Added this so your dashboard logic makes sense
        ('lab_tech', 'Lab Technician'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
    
    class Meta:
        ordering = ['-created_at']


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_verified = models.BooleanField(default=False) 
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Profile of {self.user.username}"


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    @property
    def action_color(self):
        act = self.action.lower()
        if any(word in act for word in ['deactivate', 'delete', 'remove', 'error']):
            return 'danger'
        if any(word in act for word in ['activate', 'verified', 'success', 'login']):
            return 'success'
        if 'role' in act or 'change' in act:
            return 'warning'
        return 'info'

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"


class Ward(models.Model):
    WARD_TYPES = [('General', 'General'), ('ICU', 'ICU'), ('Maternity', 'Maternity'), ('Pediatric', 'Pediatric')]
    name = models.CharField(max_length=100)
    ward_type = models.CharField(max_length=50, choices=WARD_TYPES)
    capacity = models.IntegerField(default=10)
    occupied_beds = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.ward_type})"


class MedicalRecord(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_records')
    prescription = models.TextField()
    visit_date = models.DateTimeField(auto_now_add=True)
    pharmacy_status = models.CharField(
        max_length=20, 
        choices=[('pending', 'Pending'), ('completed', 'Completed')], 
        default='pending'
    )

    def __str__(self):
        return f"Record for {self.patient.username} - {self.visit_date.date()}"


class Medicine(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, help_text="e.g., Antibiotic, Analgesic")
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level



class LabRequest(models.Model):
    # Choices for urgency
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('emergency', 'Emergency (STAT)'),
    ]

    # --- RELATIONSHIPS ---
    # Links to your Patient model (ensure the app name 'patients' is correct)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE)
    
    # Links to the User (Doctor), restricted to doctor users if using groups
    doctor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'groups__name': 'Doctor'}
    )
    
    # --- TEST DETAILS ---
    test_name = models.CharField(max_length=200)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    clinical_notes = models.TextField(
        blank=True, 
        help_text="Reason for test / symptoms (entered by Doctor)"
    )
    
    # --- RESULTS DATA (Filled by Lab Tech) ---
    findings = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='lab_results/', blank=True, null=True)
    
    # --- WORKFLOW TRACKING ---
    payment_status = models.CharField(max_length=20, default='pending') # pending, paid
    is_completed = models.BooleanField(default=False)
    
    # --- TIMESTAMPS ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.test_name} - {self.patient.name} ({self.priority})"


class Reagent(models.Model):
    name = models.CharField(max_length=100)
    stock_quantity = models.PositiveIntegerField(default=0)
    min_threshold = models.PositiveIntegerField(default=10) # Alert level
    last_restocked = models.DateTimeField(auto_now=True)

    def is_low_stock(self):
        return self.stock_quantity <= self.min_threshold

    def __str__(self):
        return self.name





class ContactMessage(models.Model):
    # Basic Info
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200) # Increased length for flexibility
    message = models.TextField()
    
    # Manager Actions
    response = models.TextField(blank=True, null=True) 
    
    # Status Tracking
    is_read = models.BooleanField(default=False)      # For the "New Message" notification
    is_resolved = models.BooleanField(default=False)  # For the "Answered" status
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures newest messages appear at the top of the dashboard
        ordering = ['-created_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.subject} - {self.name}"


class Patient(models.Model):
    # Link to the User account
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name='accounts_patient_record')
    
    # Basic Medical Info
    patient_id = models.CharField(max_length=20, unique=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True, null=True)
    
    def __name__(self):
        return self.user.get_full_name() or self.user.username

    def __str__(self):
        return f"Patient: {self.__name__()} ({self.patient_id})"
    
    # Helper to get name for templates
    @property
    def name(self):
        return self.__name__()

    def save(self, *args, **kwargs):
        # Auto-generate a Patient ID if it doesn't exist
        if not self.patient_id:
            import uuid
            self.patient_id = f"PAT-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)
