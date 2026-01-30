from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.role or request.user.role.lower() != 'manager':
            messages.error(request, 'Access denied.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
