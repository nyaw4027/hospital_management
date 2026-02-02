from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.ward_dashboard, name='ward_dashboard'),
    path('log-vitals/<int:admission_id>/', views.log_vitals, name='log_vitals'),
    path('discharge/<int:admission_id>/', views.discharge_patient, name='discharge_patient'),
]