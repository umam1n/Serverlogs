# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("register/", views.register, name="register"),
    path("enroll/", views.face_enroll, name="face_enroll"),
    path("search/", views.search_users, name="search_users"), # <-- ADD THIS LINE
    path("settings/", views.user_settings, name="user_settings"), # <-- ADD THIS LINE
    path("face-approvals/", views.face_approval_queue, name="face_approval_queue"),
    path("face-approvals/approve/<int:request_id>/", views.approve_face_change, name="approve_face_change"),
    path("face-approvals/deny/<int:request_id>/", views.deny_face_change, name="deny_face_change"),
    path("settings/re-enroll/", views.re_enroll_face, name="re_enroll_face"), # <-- ADD THIS
]