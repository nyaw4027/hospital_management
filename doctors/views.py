from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Doctor
from patients.models import Patient, Appointment, MedicalRecord
from .forms import MedicalRecordForm

@login_required
def doctor_dashboard(request):
    """Doctor dashboard with patient information"""
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied. This area is for doctors only.')
        return redirect('dashboard')
    
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        # Create doctor profile if doesn't exist
        doctor = Doctor.objects.create(
            user=request.user,
            doctor_id=f"DOC{request.user.id:05d}",
            specialization='general',
            license_number=f"LIC{request.user.id:05d}",
            qualification='MBBS',
            consultation_fee=500.00
        )
    
    # Get today's appointments
    from datetime import date
    today = date.today()
    todays_appointments = Appointment.objects.filter(
        doctor=request.user,
        appointment_date=today
    ).select_related('patient__user')
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        doctor=request.user,
        appointment_date__gte=today,
        status='scheduled'
    ).select_related('patient__user').order_by('appointment_date', 'appointment_time')[:10]
    
    # Get recent patients
    recent_patients = Patient.objects.filter(
        appointments__doctor=request.user
    ).distinct().order_by('-appointments__created_at')[:10]
    
    # Statistics
    total_appointments = Appointment.objects.filter(doctor=request.user).count()
    completed_appointments = Appointment.objects.filter(
        doctor=request.user,
        status='completed'
    ).count()
    
    context = {
        'doctor': doctor,
        'todays_appointments': todays_appointments,
        'upcoming_appointments': upcoming_appointments,
        'recent_patients': recent_patients,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
    }
    return render(request, 'doctors/dashboard.html', context)

@login_required
def doctor_patients(request):
    """View all patients"""
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    patients = Patient.objects.filter(
        appointments__doctor=request.user
    ).distinct()
    
    return render(request, 'doctors/patients.html', {'patients': patients})

@login_required
def patient_detail(request, patient_id):
    """View detailed patient information"""
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    patient = get_object_or_404(Patient, id=patient_id)
    appointments = Appointment.objects.filter(
        patient=patient,
        doctor=request.user
    ).order_by('-appointment_date')
    medical_records = MedicalRecord.objects.filter(
        patient=patient,
        doctor=request.user
    ).order_by('-visit_date')
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'medical_records': medical_records,
    }
    return render(request, 'doctors/patient_detail.html', context)

@login_required
def add_medical_record(request, patient_id):
    """Add medical record for a patient"""
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.patient = patient
            medical_record.doctor = request.user
            medical_record.save()
            messages.success(request, 'Medical record added successfully!')
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = MedicalRecordForm()
    
    return render(request, 'doctors/add_medical_record.html', {
        'form': form,
        'patient': patient
    })

@login_required
def doctor_appointments(request):
    """View all doctor appointments"""
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    appointments = Appointment.objects.filter(
        doctor=request.user
    ).select_related('patient__user').order_by('-appointment_date', '-appointment_time')
    
    return render(request, 'doctors/appointments.html', {'appointments': appointments})

@login_required
def update_appointment_status(request, appointment_id):
    """Update appointment status"""
    if request.user.role != 'doctor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes')
        
        if status in dict(Appointment.STATUS_CHOICES):
            appointment.status = status
            if notes:
                appointment.notes = notes
            appointment.save()
            messages.success(request, 'Appointment status updated successfully!')
        else:
            messages.error(request, 'Invalid status.')
    
    return redirect('doctor_appointments')