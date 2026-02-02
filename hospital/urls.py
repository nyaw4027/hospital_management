"""
Hospital Management System - Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import user_login # Import your custom login view directly
from allauth.account.views import PasswordChangeView

urlpatterns = [
    # 1. Admin Portal
    path('admin/', admin.site.urls),
    
    # 2. Custom Authentication (This fixes the "look" of the login page)
    # We define the login path EXPLICITLY at the top so it takes priority
    path('accounts/login/', user_login, name='login'),

    path('accounts/password/change/', PasswordChangeView.as_view(), name='password_change'),

    # 3. App-Specific Modules & Home
    path('', include('accounts.urls')), 
    path('doctors/', include('doctors.urls')),
    path('patients/', include('patients.urls')),
    path('cashier/', include('cashier.urls')),
    path('manager/', include('manager.urls')),

    # 4. Django Allauth (For Google Login and social features)
    # This must come AFTER your custom login path to avoid template overriding
    path('accounts/', include('allauth.urls')),

    

    path('nurse/', include('nurses.urls')),
]

# Serve media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)