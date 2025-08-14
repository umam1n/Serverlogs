from django import forms
from .models import ServerRoomAccessLog

class AccessRequestForm(forms.ModelForm):
    class Meta:
        model = ServerRoomAccessLog
        fields = [
            'location', 
            'scheduled_for_date',
            'category', 
            'notes', 
            'group_members' # This field will now be hidden
        ]
        widgets = {
            'scheduled_for_date': forms.DateInput(attrs={'type': 'date'}),
            # --- ADD THIS WIDGET ---
            'group_members': forms.HiddenInput(),
        }


class CheckInVerificationForm(forms.ModelForm):
    # This hidden field will hold the image data as a text string
    photo_data = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = ServerRoomAccessLog
        fields = [] # No other fields are needed on this form

class CheckOutForm(forms.ModelForm):
    class Meta:
        model = ServerRoomAccessLog
        fields = ['activity_report', 'outcome']