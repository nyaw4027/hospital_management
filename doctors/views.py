import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import FileResponse
from reportlab.pdfgen import canvas

# Import models from their respective apps
from .models import Doctor, Prescription, PrescriptionItem, LabRequest
from patients.models import Patient
from appointments.models import Appointment
from .models import MedicalRecord, Prescription, PrescriptionItem, LabRequest
from .forms import MedicalRecordForm, PrescriptionForm, PrescriptionItemFormSet

# --- HELPER ---
def is_doctor(user):
    """Checks if the logged-in user has the doctor role."""
    return hasattr(user, 'role') and user.role == 'doctor'

# --- DASHBOARD ---

@login_required
def doctor_dashboard(request):
    """The Doctor's Command Center - filters for patients ready from Triage."""
    if not is_doctor(request.user):
        messages.error(request, 'Access denied. Doctor role required.')
        return redirect('dashboard')
    
    # Ensure doctor profile exists
    doctor_profile, _ = Doctor.objects.get_or_create(
        user=request.user,
        defaults={'doctor_id': f"DOC{request.user.id:05d}"}
    )

    # QUEUE LOGIC: Only show patients whose vitals were captured by nurses
    ready_patients = Appointment.objects.filter(
        doctor=request.user,
        status='ready'
    ).select_related('patient__user').order_by('appointment_time')

    active_consultations = Appointment.objects.filter(
        doctor=request.user, 
        status='consulting'
    ).select_related('patient__user')

    context = {
        'doctor': doctor_profile,
        'ready_patients': ready_patients,
        'active_consultations': active_consultations,
        'total_completed': Appointment.objects.filter(doctor=request.user, status='completed').count(),
    }
    return render(request, 'doctors/dashboard.html', context)

# --- CONSULTATION SESSION (THE BRAIN) ---

@login_required
def consultation_session(request, appointment_id):
    if not is_doctor(request.user):
        return redirect('dashboard')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    doctor_profile = get_object_or_404(Doctor, user=request.user)
    patient = appointment.patient
    
    if appointment.status == 'ready':
        appointment.status = 'consulting'
        appointment.save()
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        prescription_form = PrescriptionForm(request.POST)
        formset = PrescriptionItemFormSet(request.POST)
        
        # Validate ALL forms before saving anything
        forms_are_valid = form.is_valid()
        if request.POST.get('prescribed_medicines'):
            forms_are_valid = forms_are_valid and prescription_form.is_valid() and formset.is_valid()

        if forms_are_valid:
            # 1. Save Record
            record = form.save(commit=False)
            record.patient = patient
            record.doctor = request.user # Or doctor_profile, check your model!
            record.appointment = appointment
            record.save()
            
            # 2. Lab Trigger
            if record.ordered_tests:
                LabRequest.objects.create(
                    medical_record=record,
                    test_name=f"Clinic Panel: {record.diagnosis[:50]}",
                    status='pending'
                )


            latest_vitals = Vitals.objects.filter(patient=patient).order_by('-recorded_at').first()



            # 3. Prescription Logic
            if request.POST.get('prescribed_medicines'):
                prescription = prescription_form.save(commit=False)
                prescription.medical_record = record
                prescription.patient = patient
                prescription.doctor_profile = doctor_profile
                prescription.save()
                
                formset.instance = prescription
                formset.save()
            
            # 4. Finalize
            appointment.status = 'completed'
            appointment.save()
            
            messages.success(request, f"Visit for {patient.user.get_full_name()} finalized.")
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
        'history': MedicalRecord.objects.filter(patient=patient).order_by('-visit_date')[:5]
    }
    return render(request, 'doctors/consultation.html', context)

# --- PATIENT DATA & PDF ---

@login_required
def generate_prescription_pdf(request, prescription_id):
    """Generates professional PDF for external use or printing."""
    prescription = get_object_or_404(Prescription, id=prescription_id)
    items = prescription.items.all()
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 800, "OFFICIAL MEDICAL PRESCRIPTION")
    p.setFont("Helvetica", 11)
    p.drawString(50, 775, f"Patient: {prescription.patient.user.get_full_name()}")
    p.drawString(50, 760, f"Doctor: Dr. {prescription.doctor_profile.user.get_full_name()}")
    p.drawString(450, 775, f"Date: {prescription.created_at.strftime('%d/%m/%Y')}")
    p.line(50, 750, 550, 750)
    
    y = 720
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Medication")
    p.drawString(300, y, "Dosage/Freq")
    p.drawString(500, y, "Qty")
    
    p.setFont("Helvetica", 11)
    for item in items:
        y -= 25
        p.drawString(50, y, item.medicine_name)
        p.drawString(300, y, f"{item.dosage} ({item.frequency})")
        p.drawString(500, y, str(item.quantity))
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'Rx_{prescription.id}.pdf')

@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    history = MedicalRecord.objects.filter(patient=patient).order_by('-visit_date')
    return render(request, 'doctors/patient_detail.html', {'patient': patient, 'history': history})

@login_required
def doctor_patients(request):
    patients = Patient.objects.filter(appointments__doctor=request.user).distinct()
    return render(request, 'doctors/patients_list.html', {'patients': patients})

@login_required
def update_appointment_status(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Appointment.STATUS_CHOICES):
            appointment.status = status
            appointment.save()
            messages.success(request, "Status updated.")
    return redirect('doctor_dashboard')


@login_required
def doctor_appointments(request):
    """View to list all historical and upcoming appointments for the doctor."""
    if not is_doctor(request.user):
        return redirect('dashboard')
        
    appointments = Appointment.objects.filter(
        doctor=request.user
    ).select_related('patient__user').order_by('-appointment_date', '-appointment_time')
    
    return render(request, 'doctors/appointments.html', {'appointments': appointments})


@login_required
def complete_consultation(request, visit_id):
    if request.method == 'POST':
        # 1. Send to Pharmacy
        med_name = request.POST.get('medication')
        if med_name:
            Prescription.objects.create(
                patient_id=request.POST.get('patient_id'),
                doctor=request.user.doctor_profile,
                medication_name=med_name,
                status='pending' # Goes to Cashier first
            )

        # 2. Send to Lab
        test_id = request.POST.get('test_id')
        if test_id:
            LabRequest.objects.create(
                patient_id=request.POST.get('patient_id'),
                test_type_id=test_id,
                status='pending' # Goes to Cashier first
            )
            
        messages.success(request, "Consultation completed. Orders sent to Pharmacy & Lab.")
        return redirect('doctor_dashboard')


@login_required
def patient_ehr_profile(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Fetch all medical history for this patient
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')
    lab_results = LabRequest.objects.filter(patient=patient, status='completed').order_by('-updated_at')
    
    # Calculate some quick vitals or stats if available
    context = {
        'patient': patient,
        'prescriptions': prescriptions,
        'lab_results': lab_results,
    }
    return render(request, 'doctors/patient_ehr.html', context)



