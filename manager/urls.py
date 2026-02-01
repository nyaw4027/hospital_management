from django.urls import path
from . import views
# Remove the accounts import here to keep things clean

urlpatterns = [
    path('dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('users/', views.manage_users, name='manage_users'),
    path('doctors/', views.manage_doctors, name='manage_doctors'),
    path('patients/', views.manage_patients, name='manage_patients'),
    path('reports/', views.financial_reports, name='financial_reports'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),

    # Settings Group (All pointing to manager/views.py)
    path('settings/general/', views.system_settings, name='settings_general'),
    path('settings/notifications/', views.notification_settings, name='settings_notifications'),
    path('settings/security/', views.security_settings, name='settings_security'),
    path('settings/danger/', views.danger_zone, name='settings_danger'),
    path('settings/logs/', views.email_log_list, name='email_logs'),
]