from django.db import models

# Create your models here.
from django.conf import settings


class ServerLocation(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField()
    pic = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pic_locations'
    )
    # --- ADD THESE TWO LINES ---
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