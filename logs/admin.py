from django.contrib import admin
from .models import ActivityCategory, ActivitySubCategory, ServerRoomAccessLog

@admin.register(ServerRoomAccessLog)
class ServerRoomAccessLogAdmin(admin.ModelAdmin):
    # This creates columns in the list view
    list_display = ('user', 'location', 'status', 'request_timestamp', 'approved_by')
    
    # This adds a filter sidebar
    list_filter = ('status', 'location', 'category')
    
    # This adds a search bar at the top
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'notes')
    
    # This makes certain fields read-only in the detail view
    readonly_fields = ('request_timestamp', 'entry_timestamp', 'exit_timestamp', 'approved_by')
    
    # This organizes the fields on the edit/add page
    fieldsets = (
        ('Request Info', {
            'fields': ('user', 'location', 'request_timestamp')
        }),
        ('Activity Details', {
            'fields': ('category', 'subcategory', 'notes', 'additional_persons', 'non_registered_persons')
        }),
        ('Workflow & Status', {
            'fields': ('status', 'approved_by', 'entry_timestamp', 'exit_timestamp')
        }),
        ('Completion Report', {
            'fields': ('activity_report', 'outcome', 'entry_photo')
        }),
    )

@admin.register(ActivityCategory)
class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    
@admin.register(ActivitySubCategory)
class ActivitySubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)