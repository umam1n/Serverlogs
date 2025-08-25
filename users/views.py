# users/views.py
import os
import shutil
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.files.base import ContentFile
from django.conf import settings
import requests
import base64

from .forms import CustomUserCreationForm, UserProfileUpdateForm
from .models import CustomUser, UserChangeLog, FaceChangeRequest
from configuration.models import SiteSettings
def app_view(request):
    return render(request, 'app.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Please enroll your face.')
            return redirect('face_enroll')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('site_list')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def face_enroll(request):
    settings_obj = SiteSettings.objects.first()
    camera_enabled = settings_obj.camera_verification_enabled if settings_obj else True

    if not camera_enabled:
        messages.warning(request, "Face enrollment is temporarily disabled by an administrator.")
        return render(request, 'users/face_enroll.html', {'camera_disabled': True})
    
    if request.method == 'POST':
        photo_front_data = request.POST.get('photo_front', '')
        photo_left_data = request.POST.get('photo_left', '')
        photo_right_data = request.POST.get('photo_right', '')

        if not (photo_front_data and photo_left_data and photo_right_data):
            messages.error(request, "All three photos are required for enrollment.")
            return render(request, 'users/face_enroll.html')

        try:
            photos_to_enroll = {'front.png': photo_front_data, 'left.png': photo_left_data, 'right.png': photo_right_data}
            headers = {"X-API-Key": settings.FACE_API_KEY}
            for filename, data_url in photos_to_enroll.items():
                format, imgstr = data_url.split(';base64,')
                ext = format.split('/')[-1]
                image_file = ContentFile(base64.b64decode(imgstr), name=filename)
                files = {'file': (image_file.name, image_file.read(), f'image/{ext}')}
                enroll_url = f"{settings.FACE_SERVICE_URL}/enroll/{request.user.id}"
                response = requests.post(enroll_url, files=files, headers=headers)
                response.raise_for_status()

            request.user.is_face_enrolled = True
            request.user.save()
            messages.success(request, 'Face enrollment successful! You can now request access.')
            return redirect('site_list')
        except requests.exceptions.RequestException:
            messages.error(request, 'Error: Could not connect to the verification service.')
            return render(request, 'users/face_enroll.html')
        except Exception as e:
            messages.error(request, f'An unknown error occurred: {e}')
            return render(request, 'users/face_enroll.html')
            
    return render(request, 'users/face_enroll.html', {'camera_disabled': False})

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    if query:
        # Search for users by first name, last name, or username
        users = CustomUser.objects.filter(
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(username__icontains=query)
        ).exclude(id=request.user.id)[:5] # Exclude self, limit to 5 results

        results = [{'id': user.id, 'name': user.get_full_name()} for user in users]
        return JsonResponse(results, safe=False)
    return JsonResponse([], safe=False)

@login_required
def user_settings(request):
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            changed_fields = [field for field in form.changed_data]
            if changed_fields:
                action_description = f"Updated profile fields: {', '.join(changed_fields)}."
                UserChangeLog.objects.create(user=request.user, changed_by=request.user, action=action_description)
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('user_settings')
    else:
        form = UserProfileUpdateForm(instance=request.user)

    history = UserChangeLog.objects.filter(user=request.user)
    face_request = FaceChangeRequest.objects.filter(user=request.user).first()
    context = {'form': form, 'history': history, 'face_request': face_request}
    return render(request, 'users/settings.html', context)

@login_required
def face_approval_queue(request):
    if not request.user.is_staff:
        raise PermissionDenied
    
    pending_requests = FaceChangeRequest.objects.filter(status='Pending').select_related('user')
    context = {'pending_requests': pending_requests}
    return render(request, 'users/face_approval_queue.html', context)

@login_required
def approve_face_change(request, request_id):
    if not request.user.is_staff:
        raise PermissionDenied

    change_request = get_object_or_404(FaceChangeRequest, id=request_id)
    user_to_update = change_request.user
    
    # Define paths
    pending_dir = os.path.join(settings.BASE_DIR, 'face_db_pending', str(user_to_update.id))
    final_dir = os.path.join(settings.BASE_DIR, 'face_recognition', 'face_db', str(user_to_update.id))

    # 1. Remove old photos if they exist
    if os.path.exists(final_dir):
        shutil.rmtree(final_dir)
        
    # 2. Move new photos from pending to final destination
    shutil.move(pending_dir, final_dir)

    # 3. Update the request status
    change_request.status = 'Approved'
    change_request.reviewed_by = request.user
    change_request.save()

    messages.success(request, f"Face change for {user_to_update.get_full_name()} has been approved.")
    return redirect('face_approval_queue')


@login_required
def deny_face_change(request, request_id):
    if not request.user.is_staff:
        raise PermissionDenied

    change_request = get_object_or_404(FaceChangeRequest, id=request_id)
    
    # Delete the pending photos
    pending_dir = os.path.join(settings.BASE_DIR, 'face_db_pending', str(change_request.user.id))
    if os.path.exists(pending_dir):
        shutil.rmtree(pending_dir)

    # Update the request status
    change_request.status = 'Denied'
    change_request.reviewed_by = request.user
    change_request.save()

    messages.warning(request, f"Face change for {change_request.user.get_full_name()} has been denied.")
    return redirect('face_approval_queue')

@login_required
def re_enroll_face(request):
    settings_obj = SiteSettings.objects.first()
    camera_enabled = settings_obj.camera_verification_enabled if settings_obj else True

    if not camera_enabled:
        messages.warning(request, "Face re-enrollment is temporarily disabled by an administrator.")
        return render(request, 'users/re_enroll.html', {'camera_disabled': True})
    
    if request.method == 'POST':
        photo_front_data = request.POST.get('photo_front', '')
        photo_left_data = request.POST.get('photo_left', '')
        photo_right_data = request.POST.get('photo_right', '')

        if not (photo_front_data and photo_left_data and photo_right_data):
            messages.error(request, "All three photos are required.")
            return render(request, 'users/re_enroll.html')

        try:
            pending_dir = os.path.join(settings.BASE_DIR, 'face_db_pending', str(request.user.id))
            os.makedirs(pending_dir, exist_ok=True)
            photos_to_save = {'front.png': photo_front_data, 'left.png': photo_left_data, 'right.png': photo_right_data}
            for filename, data_url in photos_to_save.items():
                format, imgstr = data_url.split(';base64,')
                image_data = base64.b64decode(imgstr)
                with open(os.path.join(pending_dir, filename), 'wb') as f:
                    f.write(image_data)
            
            FaceChangeRequest.objects.update_or_create(user=request.user, defaults={'status': 'Pending'})
            messages.success(request, 'Your request to change verification photos has been submitted for approval.')
            return redirect('user_settings')
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

    return render(request, 'users/re_enroll.html', {'camera_disabled': False})