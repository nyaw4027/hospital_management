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