from .models import ActivityLog

def log_action(user, action, details=""):
    ActivityLog.objects.create(user=user, action=action, details=details)