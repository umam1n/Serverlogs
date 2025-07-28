from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    department = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True)
    is_face_enrolled = models.BooleanField(default=False) # <-- ADD THIS LINE

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