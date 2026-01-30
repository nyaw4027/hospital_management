from django.contrib import admin
from .models import Bill, Payment

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ['bill_number', 'patient', 'bill_type', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'bill_type', 'created_at']
    search_fields = ['bill_number', 'patient__patient_id']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_reference', 'bill', 'amount', 'payment_method', 'status', 'transaction_date']
    list_filter = ['status', 'payment_method', 'transaction_date']
    search_fields = ['payment_reference', 'paystack_reference', 'bill__bill_number']