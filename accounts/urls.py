from django.urls import path
from . import views

urlpatterns = [
    # --- PUBLIC & AUTH ---
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),

    # --- DOCTOR ROUTES ---
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/prescription/new/', views.create_prescription, name='create_prescription'),
    path('doctor/request-test/', views.request_lab_test, name='request_lab_test'),
    path('doctor/patient-history/<int:patient_id>/', views.patient_history, name='patient_history'),

    # --- PHARMACY ROUTES ---
    path('pharmacy/dashboard/', views.pharmacy_dashboard, name='pharmacy_dashboard'),
    path('pharmacy/dispense/<int:prescription_id>/', views.dispense_medication, name='dispense_medication'),

    # --- CASHIER & BILLING ROUTES ---
    path('cashier/dashboard/', views.cashier_dashboard, name='cashier_dashboard'),
    path('cashier/bill/new/', views.create_bill, name='create_bill'),
    path('cashier/bill/<int:bill_id>/', views.bill_detail, name='bill_detail'),
    path('cashier/pay/<int:bill_id>/', views.process_payment, name='process_payment'),

    # --- LAB ROUTES ---
    path('lab/dashboard/', views.lab_dashboard, name='lab_dashboard'),
    path('lab/upload/<int:test_id>/', views.upload_test_result, name='upload_test_result'),

    # --- PATIENT ROUTES ---
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('my-billing/', views.patient_billing_history, name='patient_billing_history'),

    # --- MANAGER ROUTES ---
    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/users/', views.manage_users, name='manage_users'),
    path('manager/verify/<int:user_id>/', views.verify_user, name='verify_user'),
    
    # DYNAMIC STATUS & ROLE ROUTE
    # This handles: Set as Doctor, Pharmacist, Cashier, and Deactivate/Activate
    path('manager/user-status/<int:user_id>/<str:action>/', views.update_user_status, name='update_user_status'),

    path('manager/export-pdf/', views.export_activity_pdf, name='export_activity_pdf'),


    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),


    path('manager/wards/', views.manage_wards, name='manage_wards'),
    path('manager/settings/', views.system_settings, name='system_settings'),

    path('pharmacy/dashboard/', views.pharmacy_dashboard, name='pharmacy_dashboard'),
    path('pharmacy/dispense/<int:record_id>/', views.update_prescription_status, name='update_prescription_status'),
    path('pharmacy/add-stock/', views.add_medicine_stock, name='add_medicine_stock'),
    path('lab/submit/<int:test_id>/', views.submit_lab_result, name='submit_lab_result'),
    path('lab/print/<int:test_id>/', views.print_lab_report, name='print_lab_report'),
    path('patient/<int:patient_id>/order-lab/', views.create_lab_order, name='create_lab_order'),
    path('lab/result/<int:lab_id>/pdf/', views.download_lab_pdf, name='download_lab_pdf'),
    path('settings/', views.user_settings, name='settings'),
]