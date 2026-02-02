from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.nurse_dashboard, name='nurse_dashboard'),
    path('vitals/<int:appointment_id>/', views.enter_vitals, name='enter_vitals'),
]