# logs/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("request/", views.request_access, name="request_access"),
    path("history/", views.access_history, name="access_history"),
    
    path("manage/", views.manage_logs, name="manage_logs"), # Change this line
    path("approve/<int:log_id>/", views.approve_request, name="approve_request"),
    path("deny/<int:log_id>/", views.deny_request, name="deny_request"),
    
    path("check-in/<int:log_id>/", views.process_check_in, name="process_check_in"),
    path("check-out/<int:log_id>/", views.process_check_out, name="process_check_out"), # <-- ADD THIS LINE
]