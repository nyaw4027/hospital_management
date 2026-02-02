from django.urls import path
from . import views

urlpatterns = [
    # Main Dashboard
    path('dashboard/', views.cashier_dashboard, name='cashier_dashboard'),

    # General Billing & Payments
    path('create-bill/', views.create_bill, name='create_bill'),
    path('bill/<int:bill_id>/', views.bill_detail, name='bill_detail'),
    path('bill/<int:bill_id>/process-payment/', views.process_payment, name='process_payment'),
    path('verify-paystack/', views.verify_paystack_payment, name='verify_paystack_payment'),
    
    # Lab Queue & Payments
    path('mark-as-paid/<int:lab_id>/', views.mark_as_paid, name='mark_as_paid'),
    
    # Pharmacy Queue & Payments
    path('prescription/<int:prescription_id>/pay/', views.mark_prescription_paid, name='mark_prescription_paid'),

    # Reporting & History
    path('bills/', views.all_bills, name='all_bills'),
    path('payments/', views.all_payments, name='all_payments'),
    path('report/daily/', views.daily_report, name='daily_report'),

    # Receipt Generation (PDFs)
    path('payment/<int:payment_id>/receipt/', views.print_receipt, name='print_receipt'),
    path('receipt/lab/<int:lab_id>/', views.print_lab_receipt, name='print_lab_receipt'),
]