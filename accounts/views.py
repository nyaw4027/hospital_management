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
from cashier.models import Bill, Payment
from manager.models import Ward
from manager.models import HospitalSetting
from accounts.models import MedicalRecord, Medicine
from django.db.models import F
from .models import LabRequest, Reagent
from patients.models import Patient
from django.contrib import messages
from .models import ContactMessage



# accounts/views.py

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
    if not (request.user.role == 'manager' or request.user.is_superuser):
        return redirect('home')

    # 1. Capture the search and filter inputs from the URL
    query = request.GET.get('q')
    action_filter = request.GET.get('action')
    
    # 2. Start with all logs
    logs = ActivityLog.objects.all().select_related('user')

    # 3. Apply Search (if the user typed something)
    if query:
        logs = logs.filter(
            Q(user__username__icontains=query) | 
            Q(details__icontains=query)
        )
        
    # 4. Apply Action Filter (if the user clicked a dropdown item)
    if action_filter:
        logs = logs.filter(action__icontains=action_filter)

    # 5. Order and limit results
    logs = logs.order_by('-timestamp')[:50]

    context = {
        'stat_items': [
            ('Total Users', User.objects.count(), 'fa-users', 'primary'),
            ('Doctors', User.objects.filter(role='doctor').count(), 'fa-user-md', 'success'),
            ('Patients', User.objects.filter(role='patient').count(), 'fa-user-injured', 'info'),
            ('Support Staff', User.objects.filter(role__in=['pharmacy', 'cashier', 'lab']).count(), 'fa-user-tie', 'warning'),
        ],
        'logs': logs,
        'query': query, # Keeps the text in the search bar after you click search
        'current_filter': action_filter or "Filter by Action", # Updates the dropdown button label
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
    """Unified Cashier Dashboard for General Billing and Lab Payments"""
    # 1. Access Control
    if request.user.role not in ['cashier', 'manager', 'admin']:
        messages.error(request, 'Access denied. This area is for cashier staff only.')
        return redirect('dashboard')
    
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    # 2. General Billing Stats (Consultations, etc.)
    total_bills = Bill.objects.count()
    pending_general_bills = Bill.objects.filter(status='pending').count()
    
    # 3. Lab-Specific Billing
    pending_lab_bills = LabRequest.objects.filter(payment_status='pending').order_by('-created_at')
    lab_pending_count = pending_lab_bills.count()
    
    # 4. Financial Totals (Summing successful payments)
    today_payments = Payment.objects.filter(
        transaction_date__date=today,
        status='success'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    month_payments = Payment.objects.filter(
        transaction_date__date__gte=this_month_start,
        status='success'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # 5. Recent Activity Lists
    recent_bills = Bill.objects.select_related('patient__user').all().order_by('-created_at')[:10]
    
    context = {
        'total_bills': total_bills,
        'pending_general_count': pending_general_bills,
        'pending_lab_bills': pending_lab_bills,
        'lab_pending_count': lab_pending_count,
        'today_payments': today_payments,
        'month_payments': month_payments,
        'recent_bills': recent_bills,
    }
    return render(request, 'cashier/dashboard.html', context)

@login_required
def daily_report(request):
    """View to generate the printable End of Day report"""
    if request.user.role not in ['cashier', 'manager']:
        return redirect('dashboard')

    today = timezone.now().date()
    
    # Filter payments processed today
    payments = Payment.objects.filter(
        transaction_date__date=today,
        status='success'
    ).select_related('bill__patient__user')

    # Summary grouped by payment method
    method_summary = payments.values('payment_method').annotate(
        total_amount=Sum('amount'),
        count=Count('id')
    )

    total_collected = payments.aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'today': today,
        'payments': payments,
        'method_summary': method_summary,
        'total_collected': total_collected,
    }
    return render(request, 'cashier/daily_report.html', context)

@login_required
def create_bill(request):
    return render(request, 'cashier/create_bill.html')

login_required
def bill_detail(request, bill_id):
    # Fetch the actual bill object or return 404 if not found
    bill = get_object_or_404(Bill, id=bill_id)
    
    context = {
        'bill': bill,  # Pass the whole object, not just the ID
    }
    return render(request, 'cashier/bill_detail.html', context)
@login_required
def process_payment(request, bill_id):
    messages.success(request, f"Payment for Bill #{bill_id} confirmed.")
    return redirect('cashier_dashboard')

# --- LABORATORY VIEWS ---
@login_required
def lab_dashboard(request):
    # 1. Active Queue: Paid but not finished
    queue = LabRequest.objects.filter(
        payment_status='paid', 
        is_completed=False
    ).order_by('-created_at')
    
    # 2. Recently Completed: For printing/emailing
    recent_completions = LabRequest.objects.filter(
        is_completed=True
    ).order_by('-updated_at')[:5]
    
    # 3. Analytics: Monthly Test Distribution
    stats = LabRequest.objects.filter(
        created_at__month=timezone.now().month
    ).values('test_name').annotate(total=Count('id')).order_by('-total')
    
    chart_labels = [item['test_name'] for item in stats]
    chart_data = [item['total'] for item in stats]

    # FIX: Calculate sum here to avoid the 'sum' filter error in template
    total_monthly_tests = sum(chart_data)

    context = {
        'queue': queue,
        'recent_completions': recent_completions,
        'waiting_count': queue.count(),
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'total_monthly_tests': total_monthly_tests,
        'current_month_name': timezone.now().strftime('%B')
    }
    return render(request, 'lab/dashboard.html', context)

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
    # 1. Security check
    if not (request.user.is_superuser or request.user.role == 'manager'):
        messages.error(request, "Permission denied.")
        return redirect('home')

    target_user = get_object_or_404(User, id=user_id)
    
    # --- THIS WAS MISSING ---
    valid_roles = ['doctor', 'pharmacy', 'cashier', 'patient', 'lab', 'manager']
    # ------------------------
    
    if action in valid_roles:
        target_user.role = action
        target_user.save()
        
        # Auto-verify profile
        profile, created = Profile.objects.get_or_create(user=target_user)
        profile.is_verified = True
        profile.save()
        
        log_action(
            user=request.user, 
            action="Role Change", 
            details=f"Changed {target_user.username} role to {action}"
        )
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
    # 1. Define the roles allowed in your system
    # Using lowercase here to match the URL 'action' parameter
    valid_roles = ['doctor', 'manager', 'cashier', 'patient', 'pharmacy']
    
    # 2. Correctly fetch the user (using Django's standard get_object_or_404)
    target_user = get_object_or_404(User, id=user_id)
    
    # 3. Perform the update check
    if action in valid_roles:
        # Convert to upper() if your model's ROLE_CHOICES are stored in uppercase
        target_user.role = action.upper() 
        target_user.save()
        
        # LOG THIS ACTION (Ensuring audit trail for hospital security)
        # Check if log_action is imported in your views.py
        try:
            log_action(
                user=request.user, 
                action="Role Change", 
                details=f"Changed {target_user.username} role to {action.upper()}"
            )
        except NameError:
            # Fallback if log_action isn't defined yet
            pass

        messages.success(request, f"User {target_user.username} is now a {action.capitalize()}.")
    else:
        messages.error(request, f"'{action}' is not a valid clinical role.")
        
    # 4. Redirect back to the manager's user list
    return redirect('manage_users') # Ensure this matches your namespace:name

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


def privacy_policy(request):
    return render(request, 'accounts/privacy_policy.html')


@login_required
def manage_wards(request):
    if not (request.user.is_superuser or request.user.role == 'manager'):
        return redirect('home')
    wards = Ward.objects.all()
    return render(request, 'manager/manage_wards.html', {'wards': wards})

def system_settings(request):
    settings = HospitalSetting.load()
    
    if request.method == 'POST':
        settings.hospital_name = request.POST.get('hospital_name')
        settings.support_email = request.POST.get('support_email')
        settings.maintenance_mode = 'maintenance_mode' in request.POST
        settings.night_mode = 'night_mode' in request.POST
        settings.save()
        return redirect('system_settings')
        
    return render(request, 'manager/settings.html', {'settings': settings})

def send_hospital_sms(phone_number, message):
    """
    Sends an SMS via Arkesel Ghana API.
    """
    api_key = "YOUR_ARKESEL_API_KEY_HERE"  # Replace with your actual key
    sender_id = "Arkesel"  # Replace with approved Sender ID if you have one
    
    # Ensure phone number is in 233 format
    if phone_number.startswith('0'):
        phone_number = '233' + phone_number[1:]
    elif not phone_number.startswith('233'):
        phone_number = '233' + phone_number

    url = "https://sms.arkesel.com/sms/api"
    params = {
        "action": "send-sms",
        "api_key": api_key,
        "to": phone_number,
        "from": sender_id,
        "sms": message
    }
    
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"Arkesel Error: {e}")
        return None

@login_required
def verify_paystack_payment(request):
    reference = request.POST.get('reference')
    bill_id = request.POST.get('bill_id')
    bill = get_object_or_404(Bill, id=bill_id)

    # 1. Server-side Verification with Paystack
    secret_key = settings.PAYSTACK_SECRET_KEY
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        res_data = response.json()
        
        # Check if payment was truly successful on Paystack's end
        if res_data['status'] and res_data['data']['status'] == 'success':
            
            # 2. Update Bill Status
            bill.status = 'paid'
            bill.save()

            # 3. Create Record in your database
            Payment.objects.create(
                bill=bill,
                amount=bill.total_amount,
                status='success',
                payment_reference=reference,
                payment_method='paystack'
            )

            # 4. Trigger Arkesel SMS Receipt
            patient_name = bill.patient.user.first_name
            phone = bill.patient.user.phone_number
            msg = f"Receipt: Hello {patient_name}, payment of GHS {bill.total_amount} for Bill {bill.bill_number} received. Thank you."
            
            send_hospital_sms(phone, msg)

            messages.success(request, "Payment successful! Receipt sent via SMS.")
        else:
            messages.error(request, "Payment verification failed. Please contact support.")
            
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")

    return redirect('bill_detail', bill_id=bill.id)



@login_required
def all_payments(request):
    # Fetch all payments, ordering by latest first
    payments = Payment.objects.all().order_by('-transaction_date')
    
    # Ensure this string matches your folder name exactly
    return render(request, 'cashier/all_payments.html', {'payments': payments})

@login_required
def manage_wards(request):
    if request.method == 'POST':
        # Get data from the Modal form
        name = request.POST.get('name')
        ward_type = request.POST.get('ward_type')
        capacity = request.POST.get('capacity')

        # Create the object
        Ward.objects.create(
            name=name,
            ward_type=ward_type,
            capacity=capacity
        )
        messages.success(request, f"Ward '{name}' has been created successfully!")
        return redirect('manage_wards')

    # GET request: Display the wards
    wards = Ward.objects.all()
    return render(request, 'manager/manage_wards.html', {'wards': wards})


def system_settings(request):
    settings = HospitalSetting.load()
    if request.method == 'POST':
        settings.hospital_name = request.POST.get('hospital_name')
        settings.support_email = request.POST.get('support_email')
        settings.night_mode = 'night_mode' in request.POST
        settings.save()
        return redirect('settings_general')
    return render(request, 'manager/settings.html', {'settings': settings})

def notification_settings(request):
    settings = HospitalSetting.load()
    return render(request, 'manager/settings_notifications.html', {'settings': settings})

def security_settings(request):
    settings = HospitalSetting.load()
    return render(request, 'manager/settings_security.html', {'settings': settings})

def danger_zone(request):
    return render(request, 'manager/settings_danger.html')


@login_required
def pharmacy_dashboard(request):
    if request.user.role not in ['pharmacy', 'staff', 'manager'] and not request.user.is_superuser:
        return redirect('home')
    
    # 1. Get Pending Prescriptions
    prescriptions = MedicalRecord.objects.filter(pharmacy_status='pending').order_by('-visit_date')
    
    # 2. Get Inventory Items
    inventory = Medicine.objects.all()
    
    # 3. Calculate Stats
    low_stock_items = Medicine.objects.filter(quantity__lte=F('reorder_level'))

    stock_out_count = Medicine.objects.filter(quantity=0).count()
    
    context = {
        'prescriptions': prescriptions,
        'pending_count': prescriptions.count(),
        'inventory': inventory,
        'total_drugs': Medicine.objects.count(),
        'low_stock': low_stock_items.count(),
        'stock_out': stock_out_count,
        # For 'Today's Sales', you can later aggregate from a 'Sale' model
        'today_sales': "0.00", 
    }
    return render(request, 'pharmacy/dashboard.html', context)

@login_required
def update_prescription_status(request, record_id):
    if request.method == "POST":
        record = get_object_or_404(MedicalRecord, id=record_id)
        record.pharmacy_status = 'completed'
        record.save()
        messages.success(request, f"Prescription for {record.patient.user.get_full_name()} marked as dispensed.")
    
    return redirect('pharmacy_dashboard')


def add_medicine_stock(request):
    if request.method == "POST":
        name = request.POST.get('name')
        category = request.POST.get('category')
        quantity = request.POST.get('quantity')
        price = request.POST.get('price')
        reorder_level = request.POST.get('reorder_level')

        Medicine.objects.create(
            name=name,
            category=category,
            quantity=int(quantity),
            price_per_unit=float(price),
            reorder_level=int(reorder_level)
        )
        messages.success(request, f"{name} has been added to the inventory.")
    return redirect('pharmacy_dashboard')



def submit_lab_result(request, test_id):
    if request.method == 'POST':
        # 1. Fetch the request
        lab_request = get_object_or_404(LabRequest, id=test_id)
        
        # 2. Handle Inventory Deduction
        # We look for a reagent matching the test name (case-insensitive)
        reagent = Reagent.objects.filter(name__icontains=lab_request.test_name).first()
        
        if reagent:
            if reagent.stock_quantity > 0:
                reagent.stock_quantity -= 1
                reagent.save()
            else:
                messages.warning(request, f"Inventory Warning: No stock left for {reagent.name}, but results were saved.")
        
        # 3. Update Lab Request Data
        lab_request.findings = request.POST.get('findings')
        
        # Handle optional file attachment
        if request.FILES.get('attachment'):
            lab_request.attachment = request.FILES.get('attachment')
            
        lab_request.is_completed = True
        lab_request.save()
        
        # 4. Final Success Feedback
        messages.success(request, f"Results for {lab_request.patient.name} submitted and inventory updated.")
        return redirect('lab_dashboard')
    
    # Fallback for GET requests
    return redirect('lab_dashboard')



def print_lab_report(request, test_id):
    # Fetch only completed tests to ensure results are ready
    report = get_object_or_404(LabRequest, id=test_id, is_completed=True)
    
    context = {
        'report': report,
        'hospital_name': 'HMS Core Medical Center', # Customize this
        'current_date': report.created_at,
    }
    return render(request, 'lab/print_report.html', context)




def email_lab_report(request, test_id):
    report = get_object_or_404(LabRequest, id=test_id, is_completed=True)
    
    if not report.patient.email:
        messages.error(request, "This patient does not have an email address on file.")
        return redirect('lab_dashboard')

    subject = f"Medical Lab Results: {report.test_name}"
    message = f"Dear {report.patient.name},\n\nYour lab results for {report.test_name} are ready.\n\nFindings: {report.findings}\n\nBest regards,\nLab Dept."
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [report.patient.email])
        messages.success(request, f"Report emailed to {report.patient.email}")
    except Exception as e:
        messages.error(request, f"Failed to send email: {str(e)}")

    return redirect('lab_dashboard')

@login_required
def create_lab_order(request, patient_id):
    # Ensure the patient exists
    from patients.models import Patient # Adjust import as needed
    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == 'POST':
        test_name = request.POST.get('test_name')
        priority = request.POST.get('priority')
        notes = request.POST.get('clinical_notes')

        LabRequest.objects.create(
            patient=patient,
            doctor=request.user,
            test_name=test_name,
            priority=priority,
            clinical_notes=notes,
            payment_status='pending' # Flows to billing first
        )
        messages.success(request, f"Lab order for {test_name} submitted for {patient.name}.")
        return redirect('patient_detail', pk=patient.id) # Redirect back to patient profile

        return render(request, 'lab/create_order.html', {'patient': patient})




@login_required
def download_lab_pdf(request, lab_id):
    """Generates a professional PDF report for a lab result."""
    lab = get_object_or_404(LabRequest, id=lab_id)
    
    # 1. Security: Only the patient owner or medical staff (doctors/lab techs/admins)
    is_staff = request.user.role in ['doctor', 'lab_tech', 'admin']
    is_owner = (request.user.role == 'patient' and lab.patient.user == request.user)
    
    if not (is_staff or is_owner):
        return HttpResponseForbidden("You do not have permission to access this report.")

    # 2. Status Check: Patients shouldn't download incomplete reports
    if request.user.role == 'patient' and not lab.is_completed:
        return HttpResponse("This report is not yet ready for download.", status=400)

    # 3. Render HTML to PDF
    template = get_template('lab/result_pdf.html')
    # Use lab.patient.name or fallback to username if name is blank
    patient_name = lab.patient.name if lab.patient.name else lab.patient.user.username
    
    context = {
        'lab': lab,
        'patient_name': patient_name,
        'report_date': lab.updated_at,
    }
    
    html = template.render(context)
    result = io.BytesIO()
    
    # Generate PDF
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f"Lab_Result_{patient_name}_{lab.test_name}.pdf".replace(" ", "_")
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return HttpResponse("An error occurred while generating your PDF report.", status=500)



def contact_page(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Save to database
        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        
        messages.success(request, "Thank you! Your message has been sent to our administration.")
        return redirect('contact') # Ensure this matches your URL name

    return render(request, 'accounts/contact.html')




