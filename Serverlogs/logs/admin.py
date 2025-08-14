from django.contrib import admin
from .models import ActivityCategory, ActivitySubCategory, ServerRoomAccessLog

@admin.register(ServerRoomAccessLog)
class ServerRoomAccessLogAdmin(admin.ModelAdmin):
    # This creates columns in the list view
    list_display = ('user', 'location', 'scheduled_for_date', 'status', 'request_timestamp')
    
    # This adds a filter sidebar
    list_filter = ('status', 'location', 'category', 'scheduled_for_date')
    
    # This adds a search bar at the top
    search_fields = ('user_username', 'userfirst_name', 'user_last_name', 'notes')
    
    # This makes certain fields read-only in the detail view
    readonly_fields = ('request_timestamp', 'entry_timestamp', 'exit_timestamp', 'approved_by')
    
    # This organizes the fields on the edit/add page
    fieldsets = (
        ('Request Info', {
            # FIXED: Added 'scheduled_for_date' as it's a crucial request field.
            'fields': ('user', 'location', 'scheduled_for_date', 'request_timestamp')
        }),
        ('Activity & Group Details', {
            # FIXED: Replaced 'subcategory', 'additional_persons', and 'non_registered_persons'
            # with the correct field names from your model: 'group_members' and 'detailed_activities'.
            'fields': ('category', 'detailed_activities', 'group_members', 'notes')
        }),
        ('Workflow & Status', {
            'fields': ('status', 'approved_by', 'entry_timestamp', 'exit_timestamp')
        }),
        ('Completion Report', {
            # This section remains the same as the fields were already correct.
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