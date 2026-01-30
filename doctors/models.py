from django.db import models
from accounts.models import User

class Doctor(models.Model):
    """Doctor model"""
    SPECIALIZATION_CHOICES = (
        ('cardiology', 'Cardiology'),
        ('neurology', 'Neurology'),
        ('pediatrics', 'Pediatrics'),
        ('orthopedics', 'Orthopedics'),
        ('dermatology', 'Dermatology'),
        ('general', 'General Medicine'),
        ('surgery', 'Surgery'),
        ('psychiatry', 'Psychiatry'),
        ('radiology', 'Radiology'),
        ('other', 'Other'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    doctor_id = models.CharField(max_length=20, unique=True)
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES)
    license_number = models.CharField(max_length=50, unique=True)
    qualification = models.CharField(max_length=200)
    experience_years = models.IntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    availability = models.TextField(help_text="Working hours and days", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.get_specialization_display()}"
    
    class Meta:
        ordering = ['-created_at']