# appointments/models.py
from django.db import models
from django.conf import settings

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Awaiting Vitals (OPD)'),
        ('ready', 'Vitals Taken (Ready for MD)'),
        ('consulting', 'In Consultation'),
        ('lab_pending', 'Awaiting Lab Results'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    # Use strings 'app_name.ModelName' for all foreign keys to be safe
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='all_appointments')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Vitals
    temp = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    bp = models.CharField(max_length=20, blank=True, null=True)
    pulse = models.IntegerField(null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.user.get_full_name()} - {self.appointment_date}"