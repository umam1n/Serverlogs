# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from logs.models import ServerRoomAccessLog
from sites.models import ServerLocation
from datetime import date, timedelta
from django.utils import timezone
import json # Make sure json is imported

@login_required
def dashboard_view(request):
    # --- Date Filters ---
    time_filter = request.GET.get('time_filter', 'all')
    end_date = timezone.now()
    if time_filter == 'day':
        start_date = end_date - timedelta(days=1)
    elif time_filter == 'week':
        start_date = end_date - timedelta(weeks=1)
    elif time_filter == 'month':
        start_date = end_date - timedelta(days=30)
    else: # 'all'
        start_date = None

    # --- Other Filters ---
    status_filter = request.GET.get('status', '')
    site_filter = request.GET.get('site', '')

    logs = ServerRoomAccessLog.objects.select_related('user', 'location', 'category').all()

    if start_date:
        logs = logs.filter(request_timestamp__gte=start_date)
    if status_filter:
        logs = logs.filter(status=status_filter)
    if site_filter:
        logs = logs.filter(location__id=site_filter)

    # --- Calculate KPIs and Chart Data ---
    all_logs_count = logs.count()
    checked_in_count = logs.filter(status='Checked-In').count()
    completed_count = logs.filter(status='Completed').count()
    denied_count = logs.filter(status='Denied').count()
    visits_by_site = list(logs.values('location__name').annotate(count=Count('id')).order_by('-count'))
    visits_by_category = list(logs.values('category__name').annotate(count=Count('id')).order_by('-count'))

    sites_for_map = ServerLocation.objects.exclude(latitude__isnull=True, longitude__isnull=True)

    context = {
        'all_logs': logs.order_by('-request_timestamp'),
        'all_sites': ServerLocation.objects.all(),
        'all_logs_count': all_logs_count,
        'checked_in_count': checked_in_count,
        'completed_count': completed_count,
        'denied_count': denied_count,
        
        # --- PASS THE PYTHON OBJECTS DIRECTLY ---
        'visits_by_site_data': visits_by_site,
        'visits_by_category_data': visits_by_category,
        'sites_json': [
            {'name': site.name, 'lat': site.latitude, 'lon': site.longitude} 
            for site in sites_for_map
        ],
        # ----------------------------------------
        
        'site_filter': site_filter,
        'status_filter': status_filter,
        'time_filter': time_filter,
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def get_chart_data(request):
    # This view will be called by JavaScript to get updated chart data
    # ... (Logic to filter and aggregate data based on request.GET parameters) ...
    
    data = {
        'performance': { 'labels': ['Mon', 'Tue', 'Wed'], 'values': [10, 20, 15] },
        'jobTypes': { 'labels': ['Maintenance', 'Install'], 'values': [25, 10] }
    }
    return JsonResponse(data)