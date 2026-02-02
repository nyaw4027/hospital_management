# hospital/utils.py (Adjusted for your project name)
from django.core.mail import send_mail
from django.conf import settings

def check_stock_alerts():
    """Checks for medications below reorder level and notifies the manager."""
    from pharmacy.models import Medication
    low_stock_items = Medication.objects.filter(current_stock__lte=models.F('reorder_level'))
    
    if low_stock_items.exists():
        item_list = ", ".join([item.name for item in low_stock_items])
        send_mail(
            "URGENT: Low Stock Alert",
            f"The following items are low in stock: {item_list}. Please restock immediately.",
            settings.DEFAULT_FROM_EMAIL,
            ['manager@yourhospital.com'],
        )