from django.contrib import admin

# Register your models here.

# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .models import CustomUser, FaceChangeRequest # <-- Import FaceChangeRequest


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # --- ADD FIELDS TO THE DISPLAY AND FIELDSETS ---
    list_display = ['username', 'employee_id', 'email', 'first_name', 'last_name', 'company', 'is_staff', 'is_face_enrolled']
    
    fieldsets = UserAdmin.fieldsets + (
        ("Company Info", {'fields': ('employee_id', 'company', 'division', 'department', 'phone_number')}),
        ("Profile", {'fields': ('photo', 'is_face_enrolled')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Company Info", {'fields': ('employee_id', 'company', 'division', 'department', 'phone_number', 'photo')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

class FaceChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'requested_at')
    list_filter = ('status',)
    readonly_fields = ('user', 'requested_at', 'reviewed_by')

