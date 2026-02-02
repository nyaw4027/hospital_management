from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('patients/', views.doctor_patients, name='doctor_patients'),
    path('patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    
    # This matches the new professional consultation view
    path('appointment/<int:appointment_id>/consult/', views.consultation_session, name='consultation_session'),
    
    path('appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('appointment/<int:appointment_id>/update/', views.update_appointment_status, name='update_appointment_status'),
    
    # Add this for the PDF feature we built
    path('prescription/<int:prescription_id>/pdf/', views.generate_prescription_pdf, name='generate_prescription_pdf'),
]