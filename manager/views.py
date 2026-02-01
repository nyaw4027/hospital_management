from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from datetime import date, timedelta
from accounts.models import User
from patients.models import Patient, Appointment
from doctors.models import Doctor
from cashier.models import Bill, Payment
from .models import Staff
from .models import HospitalSetting, EmailLog

@login_required
def manager_dashboard(request):
    """Manager dashboard with comprehensive overview"""
    if not request.user.role or request.user.role.lower() != 'manager':
        messages.error(request, 'Access denied. This area is for managers only.')
        return redirect('home')  # avoid redirect loop
    
    # User statistics
    total_users = User.objects.count()
    total_doctors = User.objects.filter(role__iexact='doctor').count()
    total_patients = Patient.objects.count()
    total_staff = User.objects.filter(role__in=['cashier', 'staff']).count()
    
    # Appointment statistics
    today = date.today()
    total_appointments = Appointment.objects.count()
    today_appointments = Appointment.objects.filter(appointment_date=today).count()
    pending_appointments = Appointment.objects.filter(status='scheduled').count()
    
    # Financial statistics
    this_month_start = today.replace(day=1)
    total_revenue = Payment.objects.filter(status='success').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    month_revenue = Payment.objects.filter(
        transaction_date__date__gte=this_month_start,
        status='success'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    pending_bills = Bill.objects.filter(status='pending').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Recent activities
    recent_appointments = Appointment.objects.all()[:5]
    recent_payments = Payment.objects.filter(status='success')[:5]
    
    context = {
        'total_users': total_users,
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_staff': total_staff,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'total_revenue': total_revenue,
        'month_revenue': month_revenue,
        'pending_bills': pending_bills,
        'recent_appointments': recent_appointments,
        'recent_payments': recent_payments,
    }
    return render(request, 'manager/dashboard.html', context)

@login_required
def manage_users(request):
    """Manage all users"""
    if request.user.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    users = User.objects.all().order_by('-created_at')
    return render(request, 'manager/manage_users.html', {'users': users})

@login_required
def manage_doctors(request):
    """Manage doctors"""
    if request.user.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    doctors = Doctor.objects.all()
    return render(request, 'manager/manage_doctors.html', {'doctors': doctors})

@login_required
def manage_patients(request):
    """Manage patients"""
    if request.user.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    patients = Patient.objects.all()
    return render(request, 'manager/manage_patients.html', {'patients': patients})

@login_required
def financial_reports(request):
    """View financial reports"""
    if request.user.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get date range from request or default to this month
    today = date.today()
    start_date = request.GET.get('start_date', today.replace(day=1))
    end_date = request.GET.get('end_date', today)
    
    # Financial data
    payments = Payment.objects.filter(
        status='success',
        transaction_date__date__gte=start_date,
        transaction_date__date__lte=end_date
    )
    
    total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0
    payment_methods = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    bills = Bill.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    context = {
        'total_revenue': total_revenue,
        'payment_methods': payment_methods,
        'payments': payments,
        'bills': bills,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'manager/financial_reports.html', context)

@login_required
def staff_dashboard(request):
    """Staff dashboard"""
    if request.user.role != 'staff':
        messages.error(request, 'Access denied. This area is for staff only.')
        return redirect('dashboard')
    
    try:
        staff = Staff.objects.get(user=request.user)
    except Staff.DoesNotExist:
        staff = None
    
    context = {
        'staff': staff,
    }
    return render(request, 'manager/staff_dashboard.html', context)




@login_required
def system_settings(request):
    """View to manage general hospital settings"""
    if request.user.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    settings = HospitalSetting.load()
    
    if request.method == 'POST':
        settings.hospital_name = request.POST.get('hospital_name')
        settings.support_email = request.POST.get('support_email')
        # Checkboxes only send data if they are checked
        settings.maintenance_mode = 'maintenance_mode' in request.POST
        settings.night_mode = 'night_mode' in request.POST
        settings.save()
        
        messages.success(request, 'System settings updated successfully!')
        return redirect('settings_general')
        
    return render(request, 'manager/settings.html', {'settings': settings})

@login_required
def notification_settings(request):
    if request.user.role != 'manager':
        return redirect('dashboard')

    settings = HospitalSetting.load()
    
    if request.method == 'POST':
        # This handles the toggle for Email
        settings.email_notifications_enabled = 'email_enabled' in request.POST
        settings.save()
        messages.success(request, "Notification preferences updated.")
        return redirect('settings_notifications')
        
    return render(request, 'manager/settings_notifications.html', {'settings': settings})

@login_required
def security_settings(request):
    if request.user.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
        
    settings = HospitalSetting.load()
    return render(request, 'manager/settings_security.html', {'settings': settings})

def danger_zone(request):
    return render(request, 'manager/settings_danger.html')



@login_required
def email_log_list(request):
    """View to display all system email logs for the manager"""
    # Security Check: Ensure only managers can see logs
    if request.user.role != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
        
    # Get all logs, most recent first
    logs = EmailLog.objects.all().order_by('-sent_at')
    settings = HospitalSetting.load()
    
    context = {
        'logs': logs,
        'settings': settings,
    }
    return render(request, 'manager/email_logs.html', context)



@login_required
def admission_dashboard(request):
    wards = Ward.objects.annotate(
        occupied_count=Count('beds', filter=Q(beds__is_occupied=True)),
        total_count=Count('beds')
    ).all()
    
    # Calculate global stats
    total_beds = sum(w.total_count for w in wards)
    total_occupied = sum(w.occupied_count for w in wards)
    occupancy_rate = (total_occupied / total_beds * 100) if total_beds > 0 else 0

    return render(request, 'manager/admission_dashboard.html', {
        'wards': wards,
        'total_beds': total_beds,
        'total_occupied': total_occupied,
        'occupancy_rate': round(occupancy_rate, 1),
    })



# manager/views.py
@login_required
def admit_patient(request):
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        bed_id = request.POST.get('bed')
        doctor_id = request.POST.get('doctor')
        reason = request.POST.get('reason')

        # 1. Create Admission Record
        admission = Admission.objects.create(
            patient_id=patient_id,
            bed_id=bed_id,
            doctor_id=doctor_id,
            reason=reason
        )

        # 2. Update Bed Status
        bed = admission.bed
        bed.is_occupied = True
        bed.current_patient_id = patient_id
        bed.save()

        messages.success(request, f"Patient successfully admitted to {bed.bed_number}")
        return redirect('admission_dashboard')

    # GET request data
    context = {
        'patients': Patient.objects.filter(admission__isnull=True), # Only patients not already admitted
        'available_beds': Bed.objects.filter(is_occupied=False),
        'doctors': Doctor.objects.all(),
    }
    return render(request, 'manager/admit_patient.html', context)


