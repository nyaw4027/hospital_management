from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from accounts.models import Medicine

def get_inventory_alert_data():
    """Gathers data on items needing immediate attention."""
    today = timezone.now().date()
    next_month = today + timedelta(days=30)

    alerts = {
        'expired': Medicine.objects.filter(expiry_date__lte=today),
        'expiring_soon': Medicine.objects.filter(expiry_date__gt=today, expiry_date__lte=next_month),
        'low_stock': Medicine.objects.filter(quantity__lte=F('reorder_level'))
    }
    return alerts