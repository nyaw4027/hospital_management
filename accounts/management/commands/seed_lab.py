from django.core.management.base import BaseCommand
from accounts.models import LabRequest
from patients.models import Patient # Adjust if your app name is different
from django.contrib.auth.models import User
import random

class Command(BaseCommand):
    help = 'Seeds the database with 10 lab requests'

    def handle(self, *args, **kwargs):
        # Get or create a dummy doctor
        doctor, _ = User.objects.get_or_create(username='dr_tester', last_name='Arhin')
        
        # Ensure we have patients
        patients = Patient.objects.all()
        if not patients.exists():
            self.stdout.write(self.style.ERROR('No patients found. Create patients first!'))
            return

        tests = ['Malaria Parasite (MP)', 'Full Blood Count', 'Typhoid Test', 'Urinalysis', 'COVID-19 PCR']

        for _ in range(10):
            LabRequest.objects.create(
                patient=random.choice(patients),
                test_name=random.choice(tests),
                doctor=doctor,
                payment_status='paid',
                is_completed=False
            )

        self.stdout.write(self.style.SUCCESS('Successfully added 10 lab requests to the queue!'))