# manager/middleware.py
from django.shortcuts import render
from django.urls import resolve
from .models import HospitalSetting

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        settings = HospitalSetting.load()
        
        # 1. Check if maintenance mode is ON
        if settings.maintenance_mode:
            # 2. Allow Managers and Superusers to bypass
            if not (request.user.is_authenticated and request.user.role == 'manager'):
                # 3. Allow access to the login page (so you don't lock yourself out!)
                # and allow access to static files
                path = request.path
                if not any(path.startswith(p) for p in ['/accounts/login/', '/admin/', '/static/', '/media/']):
                    return render(request, 'shared/maintenance.html', status=503)

        return self.get_response(request)