from django.db import models
from accounts.models import Patient

class Vitals(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vitals')
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    
    # Clinical Data
    temperature = models.DecimalField(max_digits=4, decimal_places=1, help_text="°C")
    bp = models.CharField(max_length=15, help_text="e.g., 120/80")
    pulse = models.PositiveIntegerField(help_text="bpm")
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="kg")
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    spo2 = models.PositiveIntegerField(null=True, blank=True, verbose_name="Oxygen Saturation (%)")
    
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Vitals"

    def __str__(self):
        return f"Vitals for {self.patient.user.get_full_name()} - {self.recorded_at}"