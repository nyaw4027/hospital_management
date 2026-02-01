# utils.py
from .models import ActivityLog

def log_action(user, action, details=""):
    # Ensure we don't crash if user is somehow None
    if user and user.is_authenticated:
        ActivityLog.objects.create(
            user=user, 
            action=action, 
            details=details
        )