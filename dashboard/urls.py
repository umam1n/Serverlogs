# dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('export/', views.export_logs_csv, name='export_logs_csv'), 
    path('site-monitoring/', views.site_monitoring_view, name='site_monitoring'),
]