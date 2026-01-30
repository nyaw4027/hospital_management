"""
Hospital Management System - Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Home page
    path('', account_views.home, name='home'),

    # Authentication URLs - Primary (with /accounts/ prefix)
    path('accounts/register/', account_views.register, name='register'),
    path('accounts/login/', account_views.user_login, name='login'),
    path('accounts/logout/', account_views.user_logout, name='logout'),
    path('accounts/profile/', account_views.profile, name='profile'),
    
    # Dashboard redirect
    path('dashboard/', account_views.dashboard_redirect, name='dashboard'),

    # Django Allauth (for social authentication)
    path('accounts/', include('allauth.urls')),

    # App URLs
    path('doctors/', include('doctors.urls')),
    path('patients/', include('patients.urls')),
    path('cashier/', include('cashier.urls')),
    path('manager/', include('manager.urls')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)