from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from appointments.models import Appointment # The new, correct path

@login_required
def nurse_dashboard(request):
    pending_vitals = Appointment.objects.filter(status='pending').order_by('appointment_time')
    return render(request, 'nurses/dashboard.html', {'pending_vitals': pending_vitals})

@login_required
def enter_vitals(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        appointment.temp = request.POST.get('temp')
        appointment.bp = request.POST.get('bp')
        appointment.pulse = request.POST.get('pulse')
        appointment.respiratory_rate = request.POST.get('respiratory_rate')
        
        # Move the patient to the Doctor's queue
        appointment.status = 'ready'
        appointment.save()
        
        messages.success(request, f"Vitals for {appointment.patient.user.get_full_name()} uploaded.")
        return redirect('nurse_dashboard')
        
    return render(request, 'nurses/enter_vitals.html', {'appointment': appointment})




@login_required
def record_vitals(request, patient_id):
    if request.user.role not in ['nurse', 'doctor', 'manager']:
        return redirect('dashboard')
        
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        Vitals.objects.create(
            patient=patient,
            recorded_by=request.user,
            temperature=request.POST.get('temp'),
            bp=request.POST.get('bp'),
            pulse=request.POST.get('pulse'),
            weight=request.POST.get('weight'),
            spo2=request.POST.get('spo2')
        )
        messages.success(request, f"Vitals for {patient.user.get_full_name()} recorded.")
        return redirect('nurse_dashboard') # Or wherever you list waiting patients

    return render(request, 'nurses/record_vitals.html', {'patient': patient})


