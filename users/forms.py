from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'department', 'phone_number', 'photo')

class CustomAuthenticationForm(AuthenticationForm):
    pass

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        # Fields a user is allowed to change
        fields = ['first_name', 'last_name', 'email', 'department', 'phone_number', 'photo']