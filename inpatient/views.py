from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Ward, Admission, VitalSign
from django.utils import timezone
from math import ceil

@login_required
def ward_dashboard(request):
    # Only show patients who haven't been discharged
    active_admissions = Admission.objects.filter(is_discharged=False).select_related('patient', 'ward')
    
    # Calculate stay duration for each
    for admission in active_admissions:
        duration = timezone.now() - admission.admitted_at
        admission.days_spent = max(ceil(duration.total_seconds() / 86400), 1)
        admission.running_bill = admission.days_spent * admission.ward.rate_per_night

    context = {
        'admissions': active_admissions,
        'total_occupied': active_admissions.count(),
    }
    return render(request, 'inpatient/dashboard.html', context)



@login_required
def log_vitals(request, admission_id):
    if request.method == 'POST':
        admission = get_object_or_404(Admission, id=admission_id)
        
        VitalSign.objects.create(
            admission=admission,
            nurse=request.user,
            temperature=request.POST.get('temperature'),
            blood_pressure=request.POST.get('blood_pressure'),
            pulse_rate=request.POST.get('pulse_rate'),
            notes=request.POST.get('notes')
        )
        
        messages.success(request, f"Vitals recorded for {admission.patient.user.get_full_name()}.")
    return redirect('ward_dashboard')


@login_required
def discharge_patient(request, admission_id):
    if request.method == 'POST':
        admission = get_object_or_404(Admission, id=admission_id, is_discharged=False)
        
        # 1. Finalize the timing
        now = timezone.now()
        admission.discharged_at = now
        admission.is_discharged = True
        admission.save()

        # 2. Calculate Stay Duration
        duration = now - admission.admitted_at
        # Convert seconds to days and round up (e.g., 1.2 days becomes 2 days)
        days_spent = ceil(duration.total_seconds() / 86400)
        if days_spent < 1:
            days_spent = 1
            
        # 3. Calculate Total Cost
        total_cost = days_spent * admission.ward.rate_per_night

        # 4. Create the Bill (Integration Point)
        # Note: Replace 'Bill' with your actual billing model name
        """
        Bill.objects.create(
            patient=admission.patient,
            amount=total_cost,
            description=f"Ward Stay: {admission.ward.name} ({days_spent} days)",
            status='pending'
        )
        """

        messages.success(request, f"Patient {admission.patient.user.get_full_name()} discharged. Bill of GH₵{total_cost} generated for {days_spent} day(s).")
        
    return redirect('ward_dashboard')



