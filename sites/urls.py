# sites/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.site_list, name="site_list"),
    # Add other site-related URLs here later
]