from django.core.exceptions import PermissionDenied

def lab_tech_only(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'lab_tech':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view