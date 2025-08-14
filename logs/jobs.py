# FILE: logs/jobs.py

from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from sites.models import ServerLocation
from logs.models import ServerRoomAccessLog

def weekly_maintenance_check():
    """
    Finds sites with no completed maintenance in 30 days and notifies PICs.
    """
    print("--- Running weekly maintenance check ---")
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    overdue_sites = []
    all_pics_to_notify = set()

    for location in ServerLocation.objects.all():
        last_log = ServerRoomAccessLog.objects.filter(
            location=location, status='Completed'
        ).order_by('-exit_timestamp').first()

        # Check if the site is overdue
        if not last_log or last_log.exit_timestamp < thirty_days_ago:
            site_pics = location.pics.all()
            pic_names = ", ".join([pic.get_full_name() for pic in site_pics]) if site_pics else "No PIC Assigned"
            
            overdue_sites.append({
                'name': location.name,
                'last_activity': last_log.exit_timestamp.strftime('%d %b %Y') if last_log else "Never",
                'pic_names': pic_names
            })
            
            for pic in site_pics:
                if pic.email:
                    all_pics_to_notify.add(pic.email)

    if overdue_sites:
        recipient_list = list(all_pics_to_notify)
        if not recipient_list:
            print("Found overdue sites, but no PICs with emails to notify.")
            return

        context = {'overdue_sites': overdue_sites}
        subject = render_to_string('emails/subject_maintenance_reminder.txt', context).strip()
        html_message = render_to_string('emails/body_maintenance_reminder.html', context)
        
        send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message)
        print(f"Successfully sent maintenance reminder for {len(overdue_sites)} sites.")
    else:
        print("No overdue sites found. All clear!")