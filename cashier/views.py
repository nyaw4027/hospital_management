from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Bill, Payment
from patients.models import Patient
from .forms import BillForm, PaymentForm
import uuid
import json

@login_required
def cashier_dashboard(request):
    """Cashier dashboard"""
    if request.user.role not in ['cashier', 'manager']:
        messages.error(request, 'Access denied. This area is for cashier staff only.')
        return redirect('dashboard')
    
    # Statistics
    from django.db.models import Sum
    from datetime import date, timedelta
    
    today = date.today()
    this_month_start = today.replace(day=1)
    
    total_bills = Bill.objects.count()
    pending_bills = Bill.objects.filter(status='pending').count()
    paid_bills = Bill.objects.filter(status='paid').count()
    
    today_payments = Payment.objects.filter(
        transaction_date__date=today,
        status='success'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    month_payments = Payment.objects.filter(
        transaction_date__date__gte=this_month_start,
        status='success'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    recent_bills = Bill.objects.all()[:10]
    recent_payments = Payment.objects.filter(status='success')[:10]
    
    context = {
        'total_bills': total_bills,
        'pending_bills': pending_bills,
        'paid_bills': paid_bills,
        'today_payments': today_payments,
        'month_payments': month_payments,
        'recent_bills': recent_bills,
        'recent_payments': recent_payments,
    }
    return render(request, 'cashier/dashboard.html', context)







@login_required
def create_bill(request):
    """Create a new bill and record payment"""
    if request.user.role not in ['cashier', 'manager']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = BillForm(request.POST)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.bill_number = f"BILL{uuid.uuid4().hex[:8].upper()}"
            bill.created_by = request.user  # cashier creating the bill
            bill.status = 'pending'         # default
            bill.save()                     # SAVE the bill first

            # --- RECORD PAYMENT AFTER BILL IS SAVED ---
            payment = Payment.objects.create(
                bill=bill,
                amount=bill.total_amount,
                payment_method='cash',      # or get from form
                status='success',
                processed_by=request.user,
                payment_reference=f"PAY{uuid.uuid4().hex[:8].upper()}"
            )

            # Update bill status after payment
            bill.status = 'paid'
            bill.save()

            messages.success(request, 'Bill created and payment recorded successfully!')
            return redirect('bill_detail', bill_id=bill.id)
    else:
        form = BillForm()

    return render(request, 'cashier/create_bill.html', {'form': form})



@login_required
def bill_detail(request, bill_id):
    """View bill details"""
    if request.user.role not in ['cashier', 'manager', 'patient']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    bill = get_object_or_404(Bill, id=bill_id)
    payments = Payment.objects.filter(bill=bill)
    
    context = {
        'bill': bill,
        'payments': payments,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
    }
    return render(request, 'cashier/bill_detail.html', context)

@login_required
def process_payment(request, bill_id):
    """Process payment for a bill"""
    if request.user.role not in ['cashier', 'manager']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    bill = get_object_or_404(Bill, id=bill_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.bill = bill
            payment.payment_reference = f"PAY{uuid.uuid4().hex[:10].upper()}"
            payment.processed_by = request.user
            payment.status = 'success'  # For cash/card payments
            payment.save()
            
            # Update bill status
            total_paid = sum(p.amount for p in bill.payments.filter(status='success'))
            if total_paid >= bill.total_amount:
                bill.status = 'paid'
            elif total_paid > 0:
                bill.status = 'partially_paid'
            bill.save()
            
            messages.success(request, 'Payment processed successfully!')
            return redirect('bill_detail', bill_id=bill.id)
    else:
        form = PaymentForm()
    
    return render(request, 'cashier/process_payment.html', {
        'form': form,
        'bill': bill
    })

@login_required
def verify_paystack_payment(request):
    """Verify Paystack payment"""
    if request.method == 'POST':
        import requests
        
        reference = request.POST.get('reference')
        
        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }
        
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if data['status'] and data['data']['status'] == 'success':
                # Create payment record
                bill_id = request.POST.get('bill_id')
                bill = get_object_or_404(Bill, id=bill_id)
                
                payment = Payment.objects.create(
                    bill=bill,
                    payment_reference=f"PAY{uuid.uuid4().hex[:10].upper()}",
                    amount=data['data']['amount'] / 100,  # Paystack returns amount in kobo
                    payment_method='paystack',
                    status='success',
                    paystack_reference=reference,
                    processed_by=request.user
                )
                
                # Update bill status
                total_paid = sum(p.amount for p in bill.payments.filter(status='success'))
                if total_paid >= bill.total_amount:
                    bill.status = 'paid'
                elif total_paid > 0:
                    bill.status = 'partially_paid'
                bill.save()
                
                messages.success(request, 'Payment verified successfully!')
                return redirect('bill_detail', bill_id=bill.id)
            else:
                messages.error(request, 'Payment verification failed.')
        except Exception as e:
            messages.error(request, f'Error verifying payment: {str(e)}')
    
    return redirect('cashier_dashboard')

@login_required
def all_bills(request):
    """View all bills"""
    if request.user.role not in ['cashier', 'manager']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    bills = Bill.objects.all()
    return render(request, 'cashier/all_bills.html', {'bills': bills})

@login_required
def all_payments(request):
    """View all payments"""
    if request.user.role not in ['cashier', 'manager']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    payments = Payment.objects.filter(status='success')
    return render(request, 'cashier/all_payments.html', {'payments': payments})