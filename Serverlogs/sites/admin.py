# FILE: sites/admin.py

from django.contrib import admin
from .models import ServerLocation

@admin.register(ServerLocation)
class ServerLocationAdmin(admin.ModelAdmin):
    # MODIFIED: Added 'display_pics' to the list
    list_display = ('name', 'address', 'display_pics', 'latitude', 'longitude')
    search_fields = ('name', 'address')
    filter_horizontal = ('pics',)
    readonly_fields = ('latitude', 'longitude')

    # ADDED: A custom method to display the PICs
    def display_pics(self, obj):
        return ", ".join([pic.get_full_name() for pic in obj.pics.all()])
    display_pics.short_description = 'PICs'