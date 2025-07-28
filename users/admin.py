from django.contrib import admin

# Register your models here.

# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .models import CustomUser, FaceChangeRequest # <-- Import FaceChangeRequest


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_face_enrolled']
    # Add the field to the fieldsets to make it editable in the admin
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('department', 'phone_number', 'photo', 'is_face_enrolled')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('department', 'phone_number', 'photo')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

class FaceChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'requested_at')
    list_filter = ('status',)
    readonly_fields = ('user', 'requested_at', 'reviewed_by')

