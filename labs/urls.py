from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.lab_dashboard, name='lab_dashboard'),
    path('submit-result/<int:test_id>/', views.submit_lab_result, name='submit_lab_result'),
    path('print-report/<int:test_id>/', views.print_lab_report, name='print_lab_report'),
]