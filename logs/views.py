from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import json
from django.contrib import messages
from .models import ServerRoomAccessLog
from .forms import AccessRequestForm, CheckInVerificationForm
import requests
from django.conf import settings
import base64
from django.core.files.base import ContentFile
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from .forms import AccessRequestForm, CheckInVerificationForm, CheckOutForm
from django.contrib.auth.decorators import user_passes_test
from .utils import send_access_notification
from datetime import timedelta
from .utils import send_pic_notification
from sites.utils import is_user_in_range
from configuration.models import SiteSettings 


# --- REQUEST AND APPROVAL VIEWS ---

# FILE: logs/views.py

@login_required
def request_access(request):
    # This part handles the form submission
    if request.method == 'POST':
        form = AccessRequestForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.status = 'Pending'
            
            # Get the JSON string of checked activities from the hidden input
            activities_json = request.POST.get('detailed_activities', '[]')
            log.detailed_activities = json.loads(activities_json)
            
            # First, save the log to the database
            log.save()
            
            # THEN, send the notification email. This is the correct place.
            try:
                send_pic_notification(log, request)
            except Exception as e:
                # Log the error and notify the user, but don't crash the request.
                print(f"ERROR: Failed to send PIC notification email for log {log.id}: {e}")
                messages.warning(request, "Your access request was submitted, but we could not send a notification to the site manager. Please follow up manually if needed.")

            # Finally, add a success message and redirect the user
            messages.success(request, 'Your access request has been submitted for approval.')
            return redirect('access_history')

    # This part handles displaying the page initially (GET request)
    # or redisplaying it if the POST form was invalid.
    else:
        form = AccessRequestForm()

    # This data structure is for building the checkboxes in the template
    activity_data = {
        "fisik": {
            "name": "Physical & Environment",
            "items": [
                "Check Temperature & Humidity", "Check Cooling System (AC)", 
                "Check UPS & Power", "Check Cleanliness"
            ]
        },
        "hardware": {
            "name": "Hardware",
            "items": [
                "Visual Server Inspection", "Network Device Inspection", 
                "Storage/SAN Inspection"
            ]
        },
        "instalasi": {
            "name": "Installation & Maintenance",
            "items": [
                "Install/Remove Hardware", "Replace/Upgrade Component", 
                "Cable Management", "Physical Console Access"
            ]
        },
        "keamanan": {
            "name": "Security & Other",
            "items": [
                "Security Verification", "CCTV Check", "Accompany Third Party",
                "Asset Inventory"
            ]
        },
        "emergency": {
            "name": "Emergency",
            "items": [
                "Server Down", "Network Outage", "Power Failure", "Security Breach"
            ]
        }
    }
    
    context = {
        'form': form,
        'activity_data': activity_data
    }
    return render(request, 'logs/request_access.html', context)




@login_required
def manage_logs(request):
    if not request.user.is_staff: 
        raise PermissionDenied

    # Define the time limit for the history view
    fourteen_days_ago = timezone.now() - timedelta(days=14)

    if request.user.is_superuser:
        # Pending requests should show all, regardless of date
        pending_requests = ServerRoomAccessLog.objects.filter(status='Pending').order_by('request_timestamp')
        
        # Log history is now filtered to the last 14 days
        log_history = ServerRoomAccessLog.objects.select_related(
            'user', 'location', 'approved_by'
        ).filter(request_timestamp__gte=fourteen_days_ago)

    else: # This logic is for a staff member who is a PIC
        # Pending requests are for the sites they manage
        pending_requests = ServerRoomAccessLog.objects.filter(
            status='Pending', location__pic=request.user
        ).order_by('request_timestamp')
        
        # Log history is filtered by their sites AND the last 14 days
        log_history = ServerRoomAccessLog.objects.select_related(
            'user', 'location', 'approved_by'
        ).filter(
            location__pic=request.user, 
            request_timestamp__gte=fourteen_days_ago
        )
        
    context = {
        'pending_requests': pending_requests, 
        'log_history': log_history.order_by('-request_timestamp')
    }
    return render(request, 'logs/manage_logs.html', context)

@login_required
def approve_request(request, log_id):
    log = get_object_or_404(ServerRoomAccessLog, id=log_id)
    if not (request.user.is_superuser or log.location.pic == request.user):
        raise PermissionDenied

    log.status = 'Approved'
    log.approved_by = request.user
    log.save()

    send_access_notification(log, 'emails/subject_approved.txt', 'emails/body_approved.html')
    messages.success(request, f"Request for {log.user.get_full_name()} has been approved.")
    return redirect('manage_logs') # <-- FIX THIS LINE

@login_required
def deny_request(request, log_id):
    log = get_object_or_404(ServerRoomAccessLog, id=log_id)
    if not (request.user.is_superuser or log.location.pic == request.user):
        raise PermissionDenied

    log.status = 'Denied'
    log.approved_by = request.user
    log.save()
    send_access_notification(log, 'emails/subject_denied.txt', 'emails/body_denied.html')
    messages.warning(request, f"Request for {log.user.get_full_name()} has been denied.")
    return redirect('manage_logs') # <-- FIX THIS LINE

# --- USER WORKFLOW VIEWS ---

@login_required
def access_history(request):
    logs = ServerRoomAccessLog.objects.filter(user=request.user).order_by('-request_timestamp')
    # Pass today's date to the template for comparison
    context = {
        'logs': logs,
        'today': timezone.now().date()
    }
    return render(request, 'logs/history.html', context)

@login_required
def process_check_in(request, log_id):
    log = get_object_or_404(ServerRoomAccessLog, id=log_id, user=request.user, status='Approved')
    
    if log.scheduled_for_date != timezone.now().date():
        messages.error(request, f"Check-in is only allowed on the scheduled date of {log.scheduled_for_date.strftime('%d %b %Y')}.")
        return redirect('access_history')

    settings_obj = SiteSettings.objects.first()
    camera_enabled = settings_obj.camera_verification_enabled if settings_obj else True
    location_enabled = settings_obj.location_verification_enabled if settings_obj else True

    if request.method == 'POST':
        location_verified = False
        if not location_enabled:
            location_verified = True
            messages.info(request, "Location verification is currently disabled by an administrator.")
        else:
            try:
                user_lat = float(request.POST.get('user_latitude'))
                user_lon = float(request.POST.get('user_longitude'))
                site_location = log.location
                if is_user_in_range(user_lat, user_lon, site_location.latitude, site_location.longitude):
                    location_verified = True
                else:
                    messages.error(request, "Location Verification Failed: You are not close enough to the server room to check in.")
            except (TypeError, ValueError):
                messages.error(request, "Could not get your location. Please enable location services and try again.")
        
        if not location_verified:
            return redirect('process_check_in', log_id=log.id)

        photo_data = request.POST.get('photo_data')
        if camera_enabled and not photo_data:
            messages.error(request, "Photo is missing. Please capture a photo.")
            return redirect('process_check_in', log_id=log.id)
        
        verified = False
        if not camera_enabled:
            verified = True
            messages.info(request, "Face verification is currently disabled. Check-in approved.")
        else:
            # --- THIS IS THE FULL FACE VERIFICATION LOGIC ---
            try:
                format, imgstr = photo_data.split(';base64,')
                ext = format.split('/')[-1]
                photo_file = ContentFile(base64.b64decode(imgstr), name=f'checkin_{request.user.id}.{ext}')
                files = {'file': (photo_file.name, photo_file.read(), f'image/{ext}')}
                headers = {"X-API-Key": settings.FACE_API_KEY}
                response = requests.post(f"{settings.FACE_SERVICE_URL}/recognize", files=files, headers=headers)
                response.raise_for_status()
                data = response.json()
                if str(request.user.id) in data.get('recognized_ids', []):
                    verified = True
                else:
                    messages.error(request, "Verification Failed: Your face does not match the enrolled profile.")
            except requests.exceptions.RequestException:
                messages.error(request, "Could not connect to the verification service.")
            except Exception as e:
                messages.error(request, f"An error occurred during verification: {e}")
        
        if verified:
            log.status = 'Checked-In'
            log.entry_timestamp = timezone.now()
            if photo_data:
                format, imgstr = photo_data.split(';base64,')
                ext = format.split('/')[-1]
                photo_file = ContentFile(base64.b64decode(imgstr), name=f'checkin_{request.user.id}.{ext}')
                log.entry_photo = photo_file
            log.save()
            messages.success(request, "Verification successful. You are now checked in.")
            return redirect('access_history')
        else:
            return redirect('process_check_in', log_id=log.id)

    camera_disabled = not camera_enabled
    location_disabled = not location_enabled
    return render(request, 'logs/process_check_in.html', {'log': log, 'camera_disabled': camera_disabled, 'location_disabled': location_disabled})


@login_required
def process_check_out(request, log_id):
    # Find the active log entry for the current user
    log = get_object_or_404(ServerRoomAccessLog, id=log_id, user=request.user, status='Checked-In')
    
    if request.method == 'POST':
        form = CheckOutForm(request.POST, instance=log)
        if form.is_valid():
            checkout_log = form.save(commit=False)
            checkout_log.status = 'Completed'
            checkout_log.exit_timestamp = timezone.now()
            checkout_log.save()
            messages.success(request, "You have been successfully checked out.")
            return redirect('access_history')
    else:
        form = CheckOutForm(instance=log)

    return render(request, 'logs/process_check_out.html', {'form': form, 'log': log})

@user_passes_test(lambda u: u.is_superuser) # Only superusers can access this
def force_checkout(request, log_id):
    log = get_object_or_404(ServerRoomAccessLog, id=log_id, status='Checked-In')

    log.status = 'Completed'
    log.exit_timestamp = timezone.now()
    log.activity_report = (log.activity_report or '') + \
        f"\n\n[System Note: User was forcibly checked out by admin {request.user.username} on {timezone.now().strftime('%d %b %Y, %H:%M')}.]"

    log.save()
    messages.warning(request, f"User {log.user.get_full_name()} has been forcibly checked out.")
    return redirect('manage_logs')

