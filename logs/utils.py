# FILE: logs/utils.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse

def send_access_notification(log, subject_template_name, html_template_name):
    """
    Sends a notification email for an access log event.
    """
    if not log.user.email:
        return # Cannot send email if user has no email address

    subject = render_to_string(subject_template_name, {'log': log}).strip()
    html_message = render_to_string(html_template_name, {'log': log})
    
    send_mail(
        subject,
        '', # Plain text message (optional)
        settings.DEFAULT_FROM_EMAIL,
        [log.user.email],
        html_message=html_message,
        fail_silently=False, # Set to True in production to not crash on email errors
    )

def send_pic_notification(log, request):
    """
    Sends a notification email to ALL of the site's PICs about a new request.
    This version correctly handles the ManyToManyField.
    """
    # Get all PICs assigned to the location
    all_pics = log.location.pics.all()

    # Build a list of email addresses, but only for PICs who have one
    recipient_list = []
    for pic in all_pics:
        if pic.email:
            recipient_list.append(pic.email)

    # Only proceed if we found at least one valid email address
    if not recipient_list:
        print(f"Warning: No PICs with valid email addresses found for location '{log.location.name}'. Cannot send notification.")
        return

    manage_url = request.build_absolute_uri(reverse('manage_logs'))
    
    context = {
        'log': log,
        'manage_url': manage_url
    }
    
    subject = render_to_string('emails/subject_pic_new_request.txt', context).strip()
    html_message = render_to_string('emails/body_pic_new_request.html', context)
    
    send_mail(
        subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,  # Send to the list of all PICs
        html_message=html_message,
        fail_silently=False,
    )