from django.db import models
from accounts.models import User

class Staff(models.Model):
    """Staff model for other hospital staff"""
    DEPARTMENT_CHOICES = (
        ('administration', 'Administration'),
        ('nursing', 'Nursing'),
        ('laboratory', 'Laboratory'),
        ('pharmacy', 'Pharmacy'),
        ('reception', 'Reception'),
        ('maintenance', 'Maintenance'),
        ('security', 'Security'),
        ('other', 'Other'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    staff_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    position = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    joining_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.staff_id} - {self.user.get_full_name()}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Staff"


class Ward(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField(default=10)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class HospitalSetting(models.Model):
    hospital_name = models.CharField(max_length=200, default="HMS Core International")
    support_email = models.EmailField(default="admin@hms-core.com")
    maintenance_mode = models.BooleanField(default=False)
    night_mode = models.BooleanField(default=False)
    email_notifications_enabled = models.BooleanField(default=True) # New Field

    def save(self, *args, **kwargs):
        # This ensures only one instance exists
        self.pk = 1
        super(HospitalSetting, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Global Hospital Settings"



class EmailLog(models.Model):
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Success')
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.recipient} - {self.sent_at}"



# manager/models.py

class Bed(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=10)
    is_occupied = models.BooleanField(default=False)
    
    # Adding related_name='assigned_bed' prevents the clash
    current_patient = models.OneToOneField(
        'patients.Patient', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_bed' 
    )

    def __str__(self):
        return f"{self.ward.name} - Bed {self.bed_number}"
