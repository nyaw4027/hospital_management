import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import FileResponse
from reportlab.pdfgen import canvas
from django.db.models import Q

# Import models
from .models import Doctor, MedicalRecord, Prescription, PrescriptionItem, LabRequest
from patients.models import Patient
from appointments.models import Appointment
from .forms import MedicalRecordForm, PrescriptionForm, PrescriptionItemFormSet

# --- ACCESS CONTROL ---
def is_doctor(user):
    return hasattr(user, 'role') and user.role == 'doctor'

# Use this decorator to automatically protect views
doctor_required = user_passes_test(is_doctor, login_url='home')

# --- DASHBOARD ---

# doctors/views.py

def is_doctor(user):
    # This checks if the user is logged in AND has the role 'doctor'
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'doctor'

@login_required
@user_passes_test(is_doctor, login_url='login') # The Ultimate Gatekeeper
def doctor_dashboard(request):
    """
    Only a user with role=='doctor' will ever see the code below.
    Everyone else is redirected before this function even runs.
    """
    # Ensure the profile exists
    doctor_profile, _ = Doctor.objects.get_or_create(
        user=request.user,
        defaults={'doctor_id': f"DOC{request.user.id:05d}"}
    )

    ready_patients = Appointment.objects.filter(
        doctor=request.user,
        status='ready'
    ).select_related('patient__user').order_by('appointment_time')

    context = {
        'doctor': doctor_profile,
        'ready_patients': ready_patients,
        'total_completed': Appointment.objects.filter(doctor=request.user, status='completed').count(),
    }
    return render(request, 'doctors/dashboard.html', context)

# --- CONSULTATION SESSION ---

@login_required
@doctor_required
def consultation_session(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    patient = appointment.patient
    doctor_profile = get_object_or_404(Doctor, user=request.user)
    
    # Change status to 'consulting' as soon as the doctor opens the page
    if appointment.status == 'ready':
        appointment.status = 'consulting'
        appointment.save()
    
    # Get latest vitals for the sidebar
    latest_vitals = Vitals.objects.filter(patient=patient).order_by('-recorded_at').first()
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        prescription_form = PrescriptionForm(request.POST)
        formset = PrescriptionItemFormSet(request.POST)
        
        if form.is_valid():
            # 1. Save Medical Record
            record = form.save(commit=False)
            record.patient = patient
            record.doctor = doctor_profile
            record.appointment = appointment
            record.save()
            
            # 2. Handle Lab Requests (If tests are typed in the ordered_tests field)
            if record.ordered_tests:
                LabRequest.objects.create(
                    medical_record=record,
                    patient=patient,
                    test_name=f"Consultation Panel: {record.diagnosis[:50]}",
                    status='pending'
                )

            # 3. Handle Prescription (Only if items were added)
            if request.POST.get('has_prescription') == 'true':
                if prescription_form.is_valid() and formset.is_valid():
                    rx = prescription_form.save(commit=False)
                    rx.medical_record = record
                    rx.patient = patient
                    rx.doctor_profile = doctor_profile
                    rx.save()
                    
                    formset.instance = rx
                    formset.save()
            
            # 4. Finalize Appointment
            appointment.status = 'completed'
            appointment.save()
            
            messages.success(request, f"Consultation for {patient.user.get_full_name()} saved successfully.")
            return redirect('doctor_dashboard')
    else:
        form = MedicalRecordForm()
        prescription_form = PrescriptionForm()
        formset = PrescriptionItemFormSet()

    context = {
        'form': form,
        'prescription_form': prescription_form,
        'formset': formset,
        'appointment': appointment,
        'patient': patient,
        'vitals': latest_vitals,
        'history': MedicalRecord.objects.filter(patient=patient).order_by('-visit_date')[:5]
    }
    return render(request, 'doctors/consultation.html', context)

# --- DATA MANAGEMENT & PDF ---

@login_required
@doctor_required
def generate_prescription_pdf(request, prescription_id):
    rx = get_object_or_404(Prescription, id=prescription_id)
    items = rx.items.all()
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    
    # PDF Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, "HMS CORE - MEDICAL PRESCRIPTION")
    p.setFont("Helvetica", 11)
    p.drawString(50, 775, f"Patient: {rx.patient.user.get_full_name()}")
    p.drawString(50, 760, f"Doctor: Dr. {rx.doctor_profile.user.last_name}")
    p.drawString(450, 775, f"Date: {rx.created_at.strftime('%d/%m/%Y')}")
    p.line(50, 750, 550, 750)
    
    # Table Header
    y = 720
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Medication")
    p.drawString(250, y, "Dosage")
    p.drawString(400, y, "Frequency")
    p.drawString(500, y, "Qty")
    
    # Table Content
    p.setFont("Helvetica", 11)
    for item in items:
        y -= 25
        p.drawString(50, y, item.medicine_name[:30])
        p.drawString(250, y, item.dosage)
        p.drawString(400, y, item.frequency)
        p.drawString(500, y, str(item.quantity))
        
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'Prescription_{rx.id}.pdf')

@login_required
@doctor_required
def patient_detail(request, patient_id):
    """Full Electronic Health Record View."""
    patient = get_object_or_404(Patient, id=patient_id)
    context = {
        'patient': patient,
        'records': MedicalRecord.objects.filter(patient=patient).order_by('-visit_date'),
        'prescriptions': Prescription.objects.filter(patient=patient).order_by('-created_at'),
        'lab_results': LabRequest.objects.filter(patient=patient, status='completed').order_by('-updated_at'),
        'vitals_history': Vitals.objects.filter(patient=patient).order_by('-recorded_at')
    }
    return render(request, 'doctors/patient_ehr.html', context)

@login_required
@doctor_required
def doctor_appointments(request):
    """Historical and future appointments."""
    appointments = Appointment.objects.filter(doctor=request.user).select_related('patient__user').order_by('-appointment_date')
    return render(request, 'doctors/appointments_list.html', {'appointments': appointments})





@login_required
@doctor_required
def doctor_patients(request):
    query = request.GET.get('q')
    if query:
        # Search by name, patient_id, or phone number
        patients = Patient.objects.filter(
            Q(user__first_name__icontains=query) | 
            Q(user__last_name__icontains=query) |
            Q(patient_id__icontains=query) |
            Q(phone_number__icontains=query)
        ).distinct()
    else:
        # Show patients the doctor has recently interacted with
        patients = Patient.objects.filter(appointments__doctor=request.user).distinct()[:20]

    return render(request, 'doctors/patients_list.html', {
        'patients': patients,
        'query': query
    })


@login_required
@doctor_required
def update_appointment_status(request, appointment_id):
    """Helper view to update appointment status from the dashboard."""
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        # Only allow valid status transitions
        if new_status in ['ready', 'consulting', 'completed', 'cancelled']:
            appointment.status = new_status
            appointment.save()
            messages.success(request, f"Appointment status updated to {new_status}.")
    
    return redirect('doctor_dashboard')



