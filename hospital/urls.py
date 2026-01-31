"""
Hospital Management System - Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Admin Portal
    path('admin/', admin.site.urls),
    
    # 2. Accounts & Core Modules (Home, Auth, Pharmacy, Lab, etc.)
    # This includes the pharmacy_dashboard and lab_dashboard from your accounts/urls.py
    path('', include('accounts.urls')), 

    # 3. Django Allauth (Authentication library)
    path('accounts/', include('allauth.urls')),

    # 4. App-Specific Modules
    path('doctors/', include('doctors.urls')),
    path('patients/', include('patients.urls')),
    path('cashier/', include('cashier.urls')),
    path('manager/', include('manager.urls')),
]

# Serve media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)