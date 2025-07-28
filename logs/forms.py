from django import forms
from .models import ServerRoomAccessLog

class AccessRequestForm(forms.ModelForm):
    class Meta:
        model = ServerRoomAccessLog
        # Remove 'subcategory' and we will add 'detailed_activities' via a hidden input
        fields = ['location', 'category', 'notes', 'group_members']

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