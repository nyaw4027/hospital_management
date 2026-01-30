from django.contrib import admin
from .models import Staff

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['staff_id', 'user', 'department', 'position', 'joining_date']
    list_filter = ['department', 'joining_date']
    search_fields = ['staff_id', 'user__username', 'position']