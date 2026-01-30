from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path('appointments/', views.patient_appointments, name='patient_appointments'),
    path('medical-records/', views.patient_medical_records, name='patient_medical_records'),
]