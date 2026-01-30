from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('patients/', views.doctor_patients, name='doctor_patients'),
    path('patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patient/<int:patient_id>/add-record/', views.add_medical_record, name='add_medical_record'),
    path('appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('appointment/<int:appointment_id>/update/', views.update_appointment_status, name='update_appointment_status'),
]