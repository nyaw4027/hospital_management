from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('users/', views.manage_users, name='manage_users'),
    path('doctors/', views.manage_doctors, name='manage_doctors'),
    path('patients/', views.manage_patients, name='manage_patients'),
    path('reports/', views.financial_reports, name='financial_reports'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
]