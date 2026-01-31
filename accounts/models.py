from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('cashier', 'Cashier'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
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
    # ADD THIS LINE BELOW
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

    # --- ADD THIS PROPERTY ---
    @property
    def action_color(self):
        """Returns a Bootstrap color class based on the action type."""
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