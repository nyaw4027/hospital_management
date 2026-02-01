from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Profile, Medicine, LabRequest, ContactMessage

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Hospital Info', {'fields': ('role', 'phone_number', 'address', 'date_of_birth', 'profile_picture')}),
    )

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'reorder_level', 'stock_status')
    list_filter = ('category',)
    
    def stock_status(self, obj):
        if obj.is_low_stock:
            return format_html('<span style="color: red; font-weight: bold;">Low Stock</span>')
        return format_html('<span style="color: green;">OK</span>')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    # Changed 'is_processed' to 'is_read' to match your models.py
    list_display = ('name', 'subject', 'email', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'message')
    actions = ['mark_as_read']

    @admin.action(description="Mark selected messages as read")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

# Register the rest
admin.site.register(Profile)
admin.site.register(LabRequest)