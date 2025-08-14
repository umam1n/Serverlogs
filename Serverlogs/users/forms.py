from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # --- ADD NEW FIELDS TO THIS TUPLE ---
        fields = ('username', 'first_name', 'last_name', 'email', 'employee_id', 'company', 'division', 'department', 'phone_number', 'photo')

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        # --- ALSO ADD THEM TO THE UPDATE FORM ---
        fields = ['first_name', 'last_name', 'email', 'employee_id', 'company', 'division', 'department', 'phone_number', 'photo']
