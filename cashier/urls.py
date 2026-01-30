from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.cashier_dashboard, name='cashier_dashboard'),
    path('create-bill/', views.create_bill, name='create_bill'),
    path('bill/<int:bill_id>/', views.bill_detail, name='bill_detail'),
    path('bill/<int:bill_id>/process-payment/', views.process_payment, name='process_payment'),
    path('verify-paystack/', views.verify_paystack_payment, name='verify_paystack_payment'),
    path('bills/', views.all_bills, name='all_bills'),
    path('payments/', views.all_payments, name='all_payments'),
]