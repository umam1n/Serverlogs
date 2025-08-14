# FILE: sites/admin.py

from django.contrib import admin
from .models import ServerLocation

@admin.register(ServerLocation)
class ServerLocationAdmin(admin.ModelAdmin):
    # This list controls the columns on the main list page
    list_display = ('name', 'address', 'display_pics', 'latitude', 'longitude')
    
    search_fields = ('name', 'address')
    filter_horizontal = ('pics',) # Use a nicer widget for multiple users
    
    # These fields are still not editable by hand
    readonly_fields = ('latitude', 'longitude')

    # This function tells Django HOW to display the 'pics' field
    def display_pics(self, obj):
        # Joins the full names of all assigned PICs with a comma
        return ", ".join([pic.get_full_name() for pic in obj.pics.all()])
    
    # This sets the column header name in the admin
    display_pics.short_description = 'PICs'