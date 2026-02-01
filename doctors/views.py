from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Doctor
from patients.models import Patient, Appointment, MedicalRecord
from .forms import MedicalRecordForm

import io
from django.http import FileResponse
from reportlab.pdfgen import canvas # You'll need to pip install reportlab
from django.db.models import Q

# Helper to ensure only doctors can access these views
def is_doctor(user):
    return user.is_authenticated and user.role == 'doctor'

@login_required
def doctor_dashboard(request):
    """Doctor dashboard with daily stats and appointments"""
    if not is_doctor(request.user):
        messages.error(request, 'Access denied. This area is for doctors only.')
        return redirect('dashboard')
    
    # Use get_or_create to simplify logic and avoid explicit try/except blocks
    doctor, created = Doctor.objects.get_or_create(
        user=request.user,
        defaults={
            'doctor_id': f"DOC{request.user.id:05d}",
            'specialization': 'general',
            'license_number': f"LIC{request.user.id:05d}",
            'qualification': 'MBBS',
            'consultation_fee': 500.00
        }
    )

    today = timezone.now().date()
    
    # Optimization: select_related reduces database hits by joining tables
    todays_appointments = Appointment.objects.filter(
        doctor=request.user,
        appointment_date=today
    ).select_related('patient__user')
    
    upcoming_appointments = Appointment.objects.filter(
        doctor=request.user,
        appointment_date__gte=today,
        status='scheduled'
    ).select_related('patient__user').order_by('appointment_date', 'appointment_time')[:10]
    
    # Recent patients: distinct() ensures patients aren't listed twice
    recent_patients = Patient.objects.filter(
        appointments__doctor=request.user
    ).distinct().order_by('-appointments__created_at')[:10]
    
    # Stats
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
    if not is_doctor(request.user):
        return redirect('dashboard')
    
    patients = Patient.objects.filter(
        appointments__doctor=request.user
    ).distinct()
    
    return render(request, 'doctors/patients.html', {'patients': patients})

@login_required
def patient_detail(request, patient_id):
    if not is_doctor(request.user):
        return redirect('dashboard')
    
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Contextual data for this specific doctor and patient
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
    if not is_doctor(request.user):
        return redirect('dashboard')
    
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES) # Added request.FILES for prescriptions/scans
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
    if not is_doctor(request.user):
        return redirect('dashboard')
    
    appointments = Appointment.objects.filter(
        doctor=request.user
    ).select_related('patient__user').order_by('-appointment_date', '-appointment_time')
    
    return render(request, 'doctors/appointments.html', {'appointments': appointments})

@login_required
def update_appointment_status(request, appointment_id):
    if not is_doctor(request.user):
        return redirect('dashboard')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes')
        
        # Validate that the choice exists in the Model's STATUS_CHOICES
        if status in dict(Appointment.STATUS_CHOICES):
            appointment.status = status
            if notes:
                appointment.notes = notes
            appointment.save()
            messages.success(request, f'Appointment marked as {status}.')
        else:
            messages.error(request, 'Invalid status update attempt.')
    
    return redirect('doctor_appointments')


@login_required
def consultation_session(request, appointment_id):
    """
    The 'Heart' of the Doctor's workflow.
    Combines patient history, current appointment info, and the entry form.
    """
    if not is_doctor(request.user):
        return redirect('dashboard')
        
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    patient = appointment.patient
    
    # Get previous records to display side-by-side
    history = MedicalRecord.objects.filter(patient=patient).order_by('-visit_date')[:5]
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = patient
            record.doctor = request.user
            record.save()
            
            # Auto-complete the appointment once a record is saved
            appointment.status = 'completed'
            appointment.save()
            
            messages.success(request, f"Consultation for {patient.user.get_full_name()} completed.")
            return redirect('doctor_dashboard')
    else:
        form = MedicalRecordForm()

    return render(request, 'doctors/consultation_session.html', {
        'form': form,
        'appointment': appointment,
        'patient': patient,
        'history': history
    })

@login_required
def search_patients(request):
    """Fast AJAX-ready search for patient lookup"""
    query = request.GET.get('q', '')
    if query:
        patients = Patient.objects.filter(
            Q(user__first_name__icontains=query) | 
            Q(user__last_name__icontains=query) |
            Q(patient_id__icontains=query)
        ).distinct()
    else:
        patients = Patient.objects.none()
        
    return render(request, 'doctors/patient_search_results.html', {'patients': patients})

@login_required
def generate_prescription_pdf(request, record_id):
    """Create a professional printable PDF prescription"""
    record = get_object_or_404(MedicalRecord, id=record_id, doctor=request.user)
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    
    # PDF Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "OFFICIAL MEDICAL PRESCRIPTION")
    p.setFont("Helvetica", 12)
    p.drawString(100, 780, f"Doctor: Dr. {request.user.get_full_name()}")
    p.drawString(100, 765, f"Date: {record.visit_date}")
    
    p.line(100, 750, 500, 750)
    
    # Patient Info
    p.drawString(100, 730, f"Patient: {record.patient.user.get_full_name()}")
    p.drawString(100, 715, f"Patient ID: {record.patient.patient_id}")
    
    # Prescription Body
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 680, "Rx / Prescription:")
    p.setFont("Helvetica", 12)
    
    # Assuming your MedicalRecord model has a 'prescription' text field
    text_object = p.beginText(100, 660)
    text_object.textLines(record.prescription if record.prescription else "No medication prescribed.")
    p.drawText(text_object)
    
    # Footer/Signature line
    p.line(100, 200, 300, 200)
    p.drawString(100, 185, "Doctor's Signature")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'prescription_{record.id}.pdf')

