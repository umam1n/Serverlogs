from django.db import models

# Create your models here.
from django.conf import settings


class ServerLocation(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField()

    # --- MODIFIED FIELD ---
    pics = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='pic_locations',
        blank=True # Allows a location to have no PICs assigned
    )
    # --- END MODIFICATION ---

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name

class AccessSchedule(models.Model):
    location = models.ForeignKey(ServerLocation, on_delete=models.CASCADE)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requested_schedules')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    purpose = models.TextField()
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_schedules'
    )
    
    def __str__(self):
        return f"{self.location} access for {self.requester.username}"