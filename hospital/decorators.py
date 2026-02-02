from django.shortcuts import redirect
from django.contrib import messages

def hospital_role_required(allowed_roles):
    """
    Usage: @hospital_role_required(['lab_tech', 'manager', 'doctor'])
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Allow the specific role OR a manager
            if request.user.role in allowed_roles or request.user.role == 'manager':
                return view_func(request, *args, **kwargs)
            
            messages.error(request, f"Access Denied: Your role ({request.user.get_role_display()}) cannot access this station.")
            return redirect('main_dashboard') # Redirects to their own dashboard
        return _wrapped_view
    return decorator