# doctors/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MedicalRecord
from billing.models import Invoice # Assuming you have a billing app

@receiver(post_save, sender=MedicalRecord)
def trigger_billing(sender, instance, created, **kwargs):
    if created:
        if instance.ordered_tests or instance.prescribed_medicines:
            # Create a draft invoice for the cashier to process
            Invoice.objects.create(
                patient=instance.patient,
                related_appointment=instance.appointment,
                status='unpaid',
                total_amount=0.00 # Cashier will populate this based on specific lab/drugs
            )