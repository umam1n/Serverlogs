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

# --- REQUEST AND APPROVAL VIEWS ---

@login_required
def request_access(request):
    if request.method == 'POST':
        form = AccessRequestForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = request.user
            log.status = 'Pending'
            
            # Get the JSON string of checked activities from the hidden input
            activities_json = request.POST.get('detailed_activities', '[]')
            log.detailed_activities = json.loads(activities_json)
            
            log.save()
            messages.success(request, 'Your access request has been submitted for approval.')
            return redirect('access_history')
    else:
        form = AccessRequestForm()
    return render(request, 'logs/request_access.html', {'form': form})


@login_required
def manage_logs(request):
    if not request.user.is_staff:
        raise PermissionDenied

    # Base queryset for all logs
    log_history = ServerRoomAccessLog.objects.select_related('user', 'location', 'approved_by').all()
    
    if request.user.is_superuser:
        # Superusers see everything
        pending_requests = ServerRoomAccessLog.objects.filter(status='Pending').order_by('request_timestamp')
    else:
        # PICs see logs related to their sites
        pending_requests = ServerRoomAccessLog.objects.filter(
            status='Pending',
            location__pic=request.user
        ).order_by('request_timestamp')
        log_history = log_history.filter(location__pic=request.user)
    
    context = {
        'pending_requests': pending_requests,
        'log_history': log_history.order_by('-request_timestamp'),
    }
    return render(request, 'logs/manage_logs.html', context)
# logs/views.py

@login_required
def approve_request(request, log_id):
    log = get_object_or_404(ServerRoomAccessLog, id=log_id)
    if not (request.user.is_superuser or log.location.pic == request.user):
        raise PermissionDenied

    log.status = 'Approved'
    log.approved_by = request.user
    log.save()
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
    messages.warning(request, f"Request for {log.user.get_full_name()} has been denied.")
    return redirect('manage_logs') # <-- FIX THIS LINE

# --- USER WORKFLOW VIEWS ---

@login_required
def access_history(request):
    logs = ServerRoomAccessLog.objects.filter(user=request.user).order_by('-request_timestamp')
    return render(request, 'logs/history.html', {'logs': logs})

@login_required
def process_check_in(request, log_id):
    log = get_object_or_404(ServerRoomAccessLog, id=log_id, user=request.user, status='Approved')
    
    if request.method == 'POST':
        form = CheckInVerificationForm(request.POST)
        if form.is_valid():
            photo_data = form.cleaned_data.get('photo_data')

            if not photo_data:
                messages.error(request, "Photo is missing. Please capture a photo.")
                return render(request, 'logs/process_check_in.html', {'form': form, 'log': log})

            # --- Face Verification Logic ---
            verified = False
            try:
                # Decode the Base64 image from the form
                format, imgstr = photo_data.split(';base64,')
                ext = format.split('/')[-1]
                photo_file = ContentFile(base64.b64decode(imgstr), name=f'checkin_{request.user.id}.{ext}')
                
                # Send the photo to the face recognition service
                files = {'file': (photo_file.name, photo_file.read(), f'image/{ext}')}
                response = requests.post(f"{settings.FACE_SERVICE_URL}/recognize", files=files)
                response.raise_for_status()
                data = response.json()
                
                # Check if the current user's ID is in the list of recognized faces
                if str(request.user.id) in data.get('recognized_ids', []):
                    verified = True
                else:
                    # If the face is not a match, show an error and stop.
                    messages.error(request, "Verification Failed: Your face does not match the enrolled profile.")
                    return render(request, 'logs/process_check_in.html', {'form': form, 'log': log})

            except requests.exceptions.RequestException:
                messages.error(request, "Could not connect to the verification service.")
                return render(request, 'logs/process_check_in.html', {'form': form, 'log': log})
            except Exception:
                messages.error(request, "An error occurred while processing the verification photo.")
                return render(request, 'logs/process_check_in.html', {'form': form, 'log': log})
            
            # --- If verification is successful, complete the check-in ---
            if verified:
                log.status = 'Checked-In'
                log.entry_timestamp = timezone.now()
                log.entry_photo = photo_file # Save the verification photo
                log.save()
                messages.success(request, "Verification successful. You are now checked in.")
                return redirect('access_history')
    else:
        form = CheckInVerificationForm()

    return render(request, 'logs/process_check_in.html', {'form': form, 'log': log})

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