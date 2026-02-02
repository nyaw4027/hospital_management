import io
import uuid
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

# Local imports
from .models import Bill, Payment
from .forms import BillForm, PaymentForm




def is_cashier(user):
    return user.is_authenticated and (user.role == 'cashier' or user.role == 'manager')


@login_required
def cashier_dashboard(request):
    """Unified Cashier Dashboard with Stats, Lab Queue, and Pharmacy Queue"""
    if request.user.role not in ['cashier', 'manager']:
        messages.error(request, 'Access denied. Cashier staff only.')
        return redirect('dashboard')
    
    today = timezone.now().date()
    
    # 1. Financial Stats (KPIs)
    stats = {
        'total_bills': Bill.objects.count(),
        'pending_bills': Bill.objects.filter(status='pending').count(),
        'today_payments': Payment.objects.filter(
            transaction_date__date=today, 
            status='success'
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    # 2. Recent General Activity
    recent_bills = Bill.objects.select_related('patient__user').order_by('-id')[:10]
    
    # 3. Lab Queue (Local import to prevent circular dependency)
    from labs.models import LabRequest
    pending_lab_payments = LabRequest.objects.filter(
        payment_status='pending'
    ).select_related('patient__user')

    # 4. Pharmacy Queue (Local import to prevent circular dependency)
    from pharmacy.models import Prescription
    pending_pharmacy_payments = Prescription.objects.filter(
        status='pending'
    ).select_related('patient__user')

    context = {
        **stats,
        'recent_bills': recent_bills,
        'pending_lab_payments': pending_lab_payments,
        'pending_pharmacy_payments': pending_pharmacy_payments,
    }
    return render(request, 'cashier/dashboard.html', context)

@login_required
def create_bill(request):
    """Create a new general bill"""
    if request.user.role not in ['cashier', 'manager']:
        return redirect('dashboard')

    if request.method == 'POST':
        form = BillForm(request.POST)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.bill_number = f"BILL{uuid.uuid4().hex[:8].upper()}"
            bill.created_by = request.user
            bill.save()
            messages.success(request, f'Bill {bill.bill_number} created successfully.')
            return redirect('bill_detail', bill_id=bill.id)
    else:
        form = BillForm()
    return render(request, 'cashier/create_bill.html', {'form': form})

@login_required
def bill_detail(request, bill_id):
    """View specific bill and its payment history"""
    bill = get_object_or_404(Bill, id=bill_id)
    payments = Payment.objects.filter(bill=bill)
    return render(request, 'cashier/bill_detail.html', {
        'bill': bill, 
        'payments': payments,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY
    })

@login_required
def process_payment(request, bill_id):
    """Process manual (Cash/Check) payment for a bill"""
    bill = get_object_or_404(Bill, id=bill_id)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.bill = bill
            payment.payment_reference = f"PAY{uuid.uuid4().hex[:10].upper()}"
            payment.processed_by = request.user
            payment.status = 'success'
            payment.save()
            
            # Auto-update Bill status
            bill.status = 'paid'
            bill.save()
            
            messages.success(request, 'Payment processed successfully.')
            return redirect('bill_detail', bill_id=bill.id)
    else:
        form = PaymentForm()
    return render(request, 'cashier/process_payment.html', {'form': form, 'bill': bill})

@login_required
def verify_paystack_payment(request):
    """Verify digital payment via Paystack API"""
    if request.method == 'POST':
        reference = request.POST.get('reference')
        bill_id = request.POST.get('bill_id')
        bill = get_object_or_404(Bill, id=bill_id)
        
        headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if data['status'] and data['data']['status'] == 'success':
                Payment.objects.create(
                    bill=bill,
                    amount=data['data']['amount'] / 100,
                    payment_method='paystack',
                    status='success',
                    paystack_reference=reference,
                    processed_by=request.user
                )
                bill.status = 'paid'
                bill.save()
                messages.success(request, 'Paystack payment verified and applied.')
        except Exception as e:
            messages.error(request, f"Verification error: {str(e)}")
            
        return redirect('bill_detail', bill_id=bill.id)
    return redirect('cashier_dashboard')

@login_required
def all_bills(request):
    """List of all generated bills"""
    bills = Bill.objects.all().order_by('-id')
    return render(request, 'cashier/all_bills.html', {'bills': bills})

@login_required
def all_payments(request):
    """Log of all payment transactions"""
    payments = Payment.objects.all().order_by('-transaction_date')
    return render(request, 'cashier/all_payments.html', {'payments': payments})

@login_required
def daily_report(request):
    """End-of-day collection summary"""
    today = timezone.now().date()
    payments = Payment.objects.filter(transaction_date__date=today, status='success')
    total = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    return render(request, 'cashier/daily_report.html', {
        'payments': payments, 
        'total_collected': total, 
        'today': today
    })

@login_required
def mark_as_paid(request, lab_id):
    """Quick-pay for Lab Requests from the dashboard queue"""
    from labs.models import LabRequest
    lab = get_object_or_404(LabRequest, id=lab_id)
    
    if request.method == 'POST':
        lab.payment_status = 'paid'
        lab.save()
        
        Payment.objects.create(
            amount=getattr(lab, 'price', 0) or 0,
            payment_method='cash',
            status='success',
            processed_by=request.user,
            payment_reference=f"LAB-{lab.id}-{uuid.uuid4().hex[:4].upper()}"
        )
        messages.success(request, f"Payment recorded for {lab.test_name}.")
    return redirect('cashier_dashboard')

@login_required
def print_lab_receipt(request, lab_id):
    """Generate a PDF receipt for Lab payments"""
    from labs.models import LabRequest
    lab = get_object_or_404(LabRequest, id=lab_id)
    
    template = get_template('cashier/receipt_pdf.html')
    context = {
        'item': lab, 
        'item_type': 'Laboratory Test', 
        'amount': getattr(lab, 'price', 0), 
        'patient': lab.patient.user.get_full_name(), 
        'date': timezone.now(),
        'cashier': request.user,
        'receipt_no': f"RCP-L-{lab.id}"
    }
    
    html = template.render(context)
    result = io.BytesIO()
    pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_{lab.id}.pdf"'
    return response


@login_required
def print_receipt(request, payment_id):
    """Generate PDF Receipt for a general bill payment"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    template = get_template('cashier/receipt_pdf.html')
    context = {
        'item': payment.bill,
        'item_type': 'Medical Services/Consultation',
        'cashier': payment.processed_by,
        'receipt_no': f"RCP-{payment.id:06d}",
        'date': payment.transaction_date,
        'amount': payment.amount,
        'patient': payment.bill.patient.user.get_full_name(),
    }
    
    html = template.render(context)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Receipt_{payment.id}.pdf"'
        return response
    
    return HttpResponse("Error generating receipt", status=500)


@login_required
def mark_prescription_paid(request, prescription_id):
    """Confirm payment for a drug prescription"""
    from pharmacy.models import Prescription
    prescription = get_object_or_404(Prescription, id=prescription_id)
    
    if request.method == 'POST':
        prescription.status = 'paid'
        prescription.save()
        
        # Create a financial record
        Payment.objects.create(
            amount=prescription.price,
            payment_method='cash',
            status='success',
            processed_by=request.user,
            payment_reference=f"PHARM-{prescription.id}-{uuid.uuid4().hex[:4].upper()}"
        )
        messages.success(request, f"Payment recorded for {prescription.medication_name}.")
        
    return redirect('cashier_dashboard')



@login_required
def manager_analytics(request):
    if request.user.role != 'manager':
        return redirect('dashboard')

    # 1. Revenue by Department (Last 30 Days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    lab_rev = Payment.objects.filter(
        lab_request__isnull=False, status='success', transaction_date__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    pharmacy_rev = Payment.objects.filter(
        payment_reference__startswith='PHARM', status='success', transaction_date__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    general_rev = Payment.objects.filter(
        bill__isnull=False, status='success', transaction_date__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or 0

    # 2. Daily Revenue Trend (Last 7 Days)
    days = []
    revenue_trend = []
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        daily_sum = Payment.objects.filter(
            transaction_date__date=date, status='success'
        ).aggregate(total=Sum('amount'))['total'] or 0
        days.append(date.strftime('%a')) # 'Mon', 'Tue', etc.
        revenue_trend.append(float(daily_sum))

    context = {
        'lab_rev': float(lab_rev),
        'pharmacy_rev': float(pharmacy_rev),
        'general_rev': float(general_rev),
        'days': json.dumps(days),
        'revenue_trend': json.dumps(revenue_trend),
    }
    return render(request, 'cashier/manager_analytics.html', context)



