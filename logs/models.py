from django.db import models

# Create your models here.# logs/models.py
from django.db import models
from django.utils import timezone
from users.models import CustomUser
from sites.models import ServerLocation

class ActivityCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class ActivitySubCategory(models.Model):
    category = models.ForeignKey(ActivityCategory, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.category.name} - {self.name}"

class ServerRoomAccessLog(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Denied', 'Denied'),
        ('Checked-In', 'Checked-In'),
        ('Completed', 'Completed'),
    ]

    OUTCOME_CHOICES = [
        ('Success', 'Success'),
        ('Partial', 'Partial Success'),
        ('Failed', 'Failed'),
    ]

    # Core Info
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='access_logs')
    location = models.ForeignKey(ServerLocation, on_delete=models.CASCADE)
    group_members = models.TextField(
        blank=True, 
        help_text="Enter the full names of all group members, one per line."
    )
    
    # Timestamps
    request_timestamp = models.DateTimeField(default=timezone.now)
    entry_timestamp = models.DateTimeField(null=True, blank=True)
    exit_timestamp = models.DateTimeField(null=True, blank=True)

    # Activity Details
    category = models.ForeignKey(ActivityCategory, on_delete=models.SET_NULL, null=True)
    detailed_activities = models.JSONField(null=True, blank=True, help_text="A list of all checked activities.")
    notes = models.TextField(help_text="Describe the purpose of your visit.")
    
    # Workflow & Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_logs')

    # Check-in/out Details
    entry_photo = models.ImageField(upload_to='access_photos/check_in/', null=True, blank=True)
    activity_report = models.TextField(blank=True, help_text="Summary of activities performed.")
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, blank=True)

    def __str__(self):
        return f"Request from {self.user.username} for {self.location.name} [{self.status}]"