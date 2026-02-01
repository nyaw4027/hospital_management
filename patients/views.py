from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings as django_settings
from .models import Patient, Appointment, MedicalRecord
from .forms import AppointmentForm
from manager.models import HospitalSetting, EmailLog # Importing the global settings

from django.utils import timezone
from accounts.models import LabRequest

@login_required
def patient_dashboard(request):
    # 1. Access Control
    if request.user.role != 'patient':
        messages.error(request, 'Access denied. This area is for patients only.')
        return redirect('dashboard')
    
    # 2. Profile Auto-Creation Logic
    patient, created = Patient.objects.get_or_create(
        user=request.user,
        defaults={'patient_id': f"PAT{request.user.id:05d}"}
    )
    
    # 3. Lab Data (Ready & Processing)
    recent_lab_results = LabRequest.objects.filter(
        patient=patient, 
        is_completed=True
    ).order_by('-updated_at')[:5]

    processing_tests = LabRequest.objects.filter(
        patient=patient, 
        payment_status='paid', 
        is_completed=False
    )

    # 4. Appointments & Stats
    recent_appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date')[:5]
    
    # Counting for the top cards
    upcoming_appointments_count = Appointment.objects.filter(
        patient=patient, 
        appointment_date__gte=timezone.now()
    ).count()

    pending_payments = LabRequest.objects.filter(
        patient=patient, 
        payment_status='pending'
    ).count()

    context = {
        'patient': patient,
        'recent_lab_results': recent_lab_results,
        'processing_tests': processing_tests,
        'recent_appointments': recent_appointments,
        'upcoming_appointments_count': upcoming_appointments_count,
        'medical_records_count': LabRequest.objects.filter(patient=patient, is_completed=True).count(),
        'pending_payments': pending_payments,
    }
    
    return render(request, 'patients/dashboard.html', context)
@login_required
def book_appointment(request):
    """Book appointment view with Global Toggle, HTML Email, and Audit Logging"""
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
            
            # --- START EMAIL LOGIC WITH AUDIT TRAIL ---
            sys_settings = HospitalSetting.load()
            
            if sys_settings.email_notifications_enabled:
                subject = f"Confirmed: Appointment at {sys_settings.hospital_name}"
                try:
                    # Prepare context for the HTML template
                    context = {
                        'hospital_name': sys_settings.hospital_name,
                        'support_email': sys_settings.support_email,
                        'user_full_name': request.user.get_full_name(),
                        'appointment_date': appointment.appointment_date,
                        'status': appointment.status,
                        'dashboard_url': request.build_absolute_uri('/patients/dashboard/'),
                    }

                    # Render the HTML and Plain Text versions
                    html_message = render_to_string('emails/appointment_confirmed.html', context)
                    plain_message = strip_tags(html_message)

                    # Send the email
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=django_settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[request.user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )

                    # LOG SUCCESS TO DATABASE
                    EmailLog.objects.create(
                        recipient=request.user.email,
                        subject=subject,
                        status='Success'
                    )
                    messages.info(request, 'A confirmation email has been sent.')

                except Exception as e:
                    # LOG FAILURE TO DATABASE
                    EmailLog.objects.create(
                        recipient=request.user.email,
                        subject=subject,
                        status='Failed',
                        error_message=str(e)
                    )
                    print(f"Mail Error: {e}")
                    messages.warning(request, 'Appointment booked, but email notification failed.')
            # --- END EMAIL LOGIC ---

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
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date')
    
    return render(request, 'patients/appointments.html', {'appointments': appointments})

@login_required
def patient_medical_records(request):
    """View patient medical records"""
    if request.user.role != 'patient':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    patient = get_object_or_404(Patient, user=request.user)
    medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-visit_date')
    
    return render(request, 'patients/medical_records.html', {'medical_records': medical_records})