from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Patient, Appointment, MedicalRecord
from .forms import AppointmentForm

@login_required
def patient_dashboard(request):
    """Patient dashboard view"""
    if request.user.role != 'patient':
        messages.error(request, 'Access denied. This area is for patients only.')
        return redirect('patients/dashboard')
    
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        # Create patient profile if doesn't exist
        patient = Patient.objects.create(
            user=request.user,
            patient_id=f"PAT{request.user.id:05d}"
        )
    
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date')[:5]
    medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-visit_date')[:5]
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'medical_records': medical_records,
    }
    return render(request, 'patients/dashboard.html', context)

@login_required
def book_appointment(request):
    """Book appointment view"""
    if request.user.role != 'patient':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    patient = get_object_or_404(Patient, user=request.user)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.save()
            messages.success(request, 'Appointment booked successfully!')
            return redirect('patient_dashboard')
    else:
        form = AppointmentForm()
    
    return render(request, 'patients/book_appointment.html', {'form': form})

@login_required
def patient_appointments(request):
    """View all patient appointments"""
    if request.user.role != 'patient':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    patient = get_object_or_404(Patient, user=request.user)
    appointments = Appointment.objects.filter(patient=patient)
    
    return render(request, 'patients/appointments.html', {'appointments': appointments})

@login_required
def patient_medical_records(request):
    """View patient medical records"""
    if request.user.role != 'patient':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    patient = get_object_or_404(Patient, user=request.user)
    medical_records = MedicalRecord.objects.filter(patient=patient)
    
    return render(request, 'patients/medical_records.html', {'medical_records': medical_records})