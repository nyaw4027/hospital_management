from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from .models import User, Profile
from .forms import UserRegistrationForm, UserLoginForm
from .utils import log_action
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import ActivityLog

# --- PUBLIC VIEWS ---
def home(request):
    return render(request, 'accounts/home.html')

def about(request):
    return render(request, 'accounts/about.html')

def contact(request): 
    return render(request, 'accounts/contact.html')

def services(request): 
    return render(request, 'accounts/service.html')

# --- AUTHENTICATION ---
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            Profile.objects.get_or_create(user=user)
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user() 
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'This account has been deactivated.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('home')

# --- DASHBOARD LOGIC (Traffic Controller) ---
@login_required
def dashboard_redirect(request):
    role = request.user.role.lower() if request.user.role else None

    if request.user.is_superuser or role == 'manager':
        return redirect('manager_dashboard')
    
    role_map = {
        'doctor': 'doctor_dashboard',
        'patient': 'patient_dashboard',
        'pharmacy': 'pharmacy_dashboard',
        'staff': 'pharmacy_dashboard',
        'cashier': 'cashier_dashboard',
        'lab': 'lab_dashboard',
    }
    
    target_view = role_map.get(role)
    if target_view:
        return redirect(target_view)
    
    messages.warning(request, 'No specific dashboard assigned to your role.')
    return redirect('profile')

# --- MANAGER & ANALYTICS ---
@login_required
def manager_dashboard(request):
    if request.user.role != 'manager' and not request.user.is_superuser:
        return redirect('home')

    logs = ActivityLog.objects.all().select_related('user').order_by('-timestamp')[:10]

    context = {
        'stat_items': [
            ('Total Users', User.objects.count(), 'fa-users', 'primary'),
            ('Doctors', User.objects.filter(role='doctor').count(), 'fa-user-md', 'success'),
            ('Patients', User.objects.filter(role='patient').count(), 'fa-user-injured', 'info'),
            ('Support Staff', User.objects.filter(role__in=['pharmacy', 'cashier', 'lab']).count(), 'fa-user-tie', 'warning'),
        ],
        'total_revenue': 45200.50,
        'pending_bills': 3200.75,
        'logs': logs,
    }
    return render(request, 'manager/dashboard.html', context)

@login_required
def manage_users(request):
    if not (request.user.is_superuser or request.user.role == 'manager'):
        return redirect('dashboard')
    query = request.GET.get('search', '')
    users = User.objects.all().order_by('-date_joined')
    if query:
        users = users.filter(username__icontains=query) | users.filter(email__icontains=query)
    return render(request, 'manager/manage_users.html', {'users': users})

@login_required
def verify_user(request, user_id):
    # Security check: only managers or superusers allowed
    if request.user.role == 'manager' or request.user.is_superuser:
        target_user = get_object_or_404(User, id=user_id)
        
        # This prevents the RelatedObjectDoesNotExist error
        profile, created = Profile.objects.get_or_create(user=target_user)
        
        profile.is_verified = True
        profile.save()
        
        messages.success(request, f"User {target_user.username} verified successfully.")
    else:
        messages.error(request, "Unauthorized access.")
        
    return redirect('manage_users')

# --- DOCTOR VIEWS ---
@login_required
def doctor_dashboard(request):
    if request.user.role != 'doctor' and not request.user.is_superuser:
        return redirect('home')
    return render(request, 'doctor/dashboard.html')

@login_required
def create_prescription(request):
    if request.user.role != 'doctor' and not request.user.is_superuser:
        return redirect('home')
    
    if request.method == 'POST':
        medicines = request.POST.getlist('medicine_name[]')
        messages.success(request, f"Prescription issued! Sent to Billing.")
        return redirect('doctor_dashboard')

    patients = User.objects.filter(role='patient')
    return render(request, 'doctor/create_prescription.html', {'patients': patients})

@login_required
def request_lab_test(request):
    if request.user.role != 'doctor' and not request.user.is_superuser:
        return redirect('home')
    patients = User.objects.filter(role='patient')
    return render(request, 'doctor/request_test.html', {'patients': patients})

@login_required
def patient_history(request, patient_id):
    """View to see a specific patient's medical history."""
    if request.user.role != 'doctor' and not request.user.is_superuser:
        return redirect('home')
    patient = get_object_or_404(User, id=patient_id, role='patient')
    return render(request, 'doctor/patient_history.html', {'patient': patient})

# --- CASHIER & BILLING VIEWS ---
@login_required
def cashier_dashboard(request):
    if request.user.role not in ['cashier', 'manager'] and not request.user.is_superuser:
        return redirect('home')

    context = {
        'pending_bills': 12,
        'today_payments': "1,450.00",
        'month_payments': "24,800.00",
        'recent_payments': [
            {'payment_reference': 'RCPT-8821', 'amount': '250.00', 'method': 'Mobile Money', 'time': '10:15 AM'},
            {'payment_reference': 'RCPT-8820', 'amount': '120.00', 'method': 'Cash', 'time': '09:45 AM'},
        ],
    }
    return render(request, 'cashier/dashboard.html', context)

@login_required
def create_bill(request):
    return render(request, 'cashier/create_bill.html')

@login_required
def bill_detail(request, bill_id):
    return render(request, 'cashier/bill_detail.html', {'bill_id': bill_id})

@login_required
def process_payment(request, bill_id):
    messages.success(request, f"Payment for Bill #{bill_id} confirmed.")
    return redirect('cashier_dashboard')

# --- LABORATORY VIEWS ---
@login_required
def lab_dashboard(request):
    if request.user.role not in ['lab', 'manager'] and not request.user.is_superuser:
        return redirect('home')

    lab_requests = [
        {'id': 1, 'patient_name': 'Abena Mansa', 'test_name': 'Malaria Parasite (MP)', 'priority': 'High'},
        {'id': 2, 'patient_name': 'Kwame Mensah', 'test_name': 'Full Blood Count (FBC)', 'priority': 'Normal'}
    ]
    return render(request, 'lab/dashboard.html', {'lab_requests': lab_requests, 'waiting_count': len(lab_requests)})

@login_required
def upload_test_result(request, test_id):
    messages.success(request, f"Test results for Request #{test_id} submitted.")
    return redirect('lab_dashboard')

# --- PHARMACY VIEWS ---
@login_required
def pharmacy_dashboard(request):
    if request.user.role not in ['pharmacy', 'staff', 'manager'] and not request.user.is_superuser:
        return redirect('home')
    
    context = {'total_drugs': 1240, 'low_stock': 8, 'today_sales': 4200, 'pending_count': 15}
    return render(request, 'pharmacy/dashboard.html', context)

@login_required
def dispense_medication(request, prescription_id):
    messages.success(request, f"Medication #{prescription_id} dispensed.")
    return redirect('pharmacy_dashboard')

# --- PATIENT VIEWS ---
@login_required
def patient_dashboard(request):
    if request.user.role != 'patient' and not request.user.is_superuser:
        return redirect('home')
    return render(request, 'patient/dashboard.html')

@login_required
def patient_billing_history(request):
    return render(request, 'patient/billing_history.html')

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')


@login_required
def update_user_status(request, user_id, action):
    if not (request.user.is_superuser or request.user.role == 'manager'):
        messages.error(request, "Permission denied.")
        return redirect('home')

    target_user = get_object_or_404(User, id=user_id)
    valid_roles = ['doctor', 'pharmacy', 'cashier', 'patient', 'lab']
    
    if action in valid_roles:
        # 1. Update the Role
        target_user.role = action
        target_user.save()
        
        # 2. AUTO-VERIFY logic starts here
        # This ensures the badge turns green immediately
        profile, created = Profile.objects.get_or_create(user=target_user)
        profile.is_verified = True
        profile.save()
        
        messages.success(request, f"User {target_user.username} is now a verified {action.capitalize()}.")
    
    elif action == 'deactivate':
        target_user.is_active = False
        target_user.save()
        messages.warning(request, f"User {target_user.username} deactivated.")
        
    elif action == 'activate':
        target_user.is_active = True
        target_user.save()
        messages.success(request, f"User {target_user.username} reactivated.")

    return redirect('manage_users')




@login_required
def update_user_status(request, user_id, action):
    # ... your existing security checks ...
    target_user = get_object_or_404(User, id=user_id)
    
    if action in valid_roles:
        target_user.role = action
        target_user.save()
        
        # LOG THIS ACTION
        log_action(
            user=request.user, 
            action="Role Change", 
            details=f"Changed {target_user.username} role to {action}"
        )
        
        # ... rest of your code ...

@login_required
def export_activity_pdf(request):
    """Generates a PDF report of recent system activities."""
    if not (request.user.is_superuser or request.user.role == 'manager'):
        return HttpResponse("Unauthorized", status=401)

    logs = ActivityLog.objects.all().select_related('user')[:50] 
    template_path = 'manager/activity_report_pdf.html'
    context = {'logs': logs, 'title': 'System Activity Report'}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="activity_report.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
       return HttpResponse('Error creating PDF report <pre>' + html + '</pre>')
    return response
