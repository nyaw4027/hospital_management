from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.pharmacy_dashboard, name='pharmacy_dashboard'),
    path('add-stock/', views.add_medicine_stock, name='add_medicine_stock'),
    path('dispense/<int:record_id>/', views.update_prescription_status, name='update_prescription_status'),
    path('inventory-report/', views.generate_inventory_report, name='generate_inventory_report'),
]