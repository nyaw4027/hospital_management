from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin"""
    list_display = ['username', 'email', 'role', 'first_name', 'last_name', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'address', 'date_of_birth', 'profile_picture')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'email')}),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Profile admin"""
    list_display = ['user', 'emergency_contact', 'blood_group']
    search_fields = ['user__username', 'user__email']