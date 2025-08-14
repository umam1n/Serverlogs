from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    company = models.CharField(max_length=150, blank=True)
    division = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True)
    is_face_enrolled = models.BooleanField(default=False)

    def __str__(self):
        return self.get_full_name() or self.username

class FaceChangeRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Denied', 'Denied'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_face_changes')

    def __str__(self):
        return f"Face change request for {self.user.username}"


# --- ADD THIS NEW MODEL AT THE BOTTOM ---
class UserChangeLog(models.Model):
    """Logs significant changes to a user's profile."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='change_logs')
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='made_changes')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=255, help_text="Description of the change made.")
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Change for {self.user.username} at {self.timestamp.strftime('%d %b %Y, %H:%M')}"