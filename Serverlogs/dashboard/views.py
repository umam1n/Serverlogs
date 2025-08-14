# dashboard/views.py
from django.db.models import Count, Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from logs.models import ServerRoomAccessLog, ActivityCategory
from sites.models import ServerLocation
from datetime import date, timedelta
from django.utils import timezone
import json # Make sure json is imported
import csv
from django.http import HttpResponse


@login_required
def dashboard_view(request):
    time_filter = request.GET.get('time_filter', 'all')
    end_date = timezone.now()
    if time_filter == 'day':
        start_date = end_date - timedelta(days=1)
    elif time_filter == 'week':
        start_date = end_date - timedelta(weeks=1)
    elif time_filter == 'month':
        start_date = end_date - timedelta(days=30)
    else:
        start_date = None

    status_filter = request.GET.get('status', '')
    site_filter = request.GET.get('site', '')
    category_filter = request.GET.get('category', '')
    user_search = request.GET.get('user_search', '')

    logs = ServerRoomAccessLog.objects.select_related('user', 'location', 'category').all()

    if start_date:
        logs = logs.filter(request_timestamp__gte=start_date)
    if status_filter:
        logs = logs.filter(status=status_filter)
    if site_filter:
        logs = logs.filter(location__id=site_filter)
    if category_filter:
        logs = logs.filter(category__id=category_filter)
    if user_search:
        logs = logs.filter(
            Q(user__first_name__icontains=user_search) |
            Q(user__last_name__icontains=user_search) |
            Q(user__username__icontains=user_search)
        )
    
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
        'all_categories': ActivityCategory.objects.all(),
        'all_logs_count': all_logs_count,
        'checked_in_count': checked_in_count,
        'completed_count': completed_count,
        'denied_count': denied_count,
        
        # --- FIX: Pass the raw Python objects, NOT a JSON string ---
        'visits_by_site_data': visits_by_site,
        'visits_by_category_data': visits_by_category,
        'sites_json': [
            {'name': site.name, 'lat': site.latitude, 'lon': site.longitude} 
            for site in sites_for_map
        ],
        
        'site_filter': site_filter,
        'status_filter': status_filter,
        'time_filter': time_filter,
        'category_filter': category_filter,
        'user_search': user_search,
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

@login_required
def export_logs_csv(request):
    # This view uses the same filtering logic as the main dashboard
    time_filter = request.GET.get('time_filter', 'all')
    status_filter = request.GET.get('status', '')
    site_filter = request.GET.get('site', '')

    # (Filtering logic copied from dashboard_view)
    logs = ServerRoomAccessLog.objects.select_related('user', 'location', 'category').all()
    end_date = timezone.now()
    if time_filter == 'day':
        start_date = end_date - timedelta(days=1)
        logs = logs.filter(request_timestamp__gte=start_date)
    elif time_filter == 'week':
        start_date = end_date - timedelta(weeks=1)
        logs = logs.filter(request_timestamp__gte=start_date)
    elif time_filter == 'month':
        start_date = end_date - timedelta(days=30)
        logs = logs.filter(request_timestamp__gte=start_date)
    if status_filter:
        logs = logs.filter(status=status_filter)
    if site_filter:
        logs = logs.filter(location__id=site_filter)

    # Create the HTTP response with CSV headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="server_room_logs.csv"'

    writer = csv.writer(response)
    # Write the header row
    writer.writerow([
        'User', 'Site', 'Status', 'Date Requested', 'Date In', 'Date Out', 
        'Purpose', 'Group Members', 'Activity Report', 'Outcome'
    ])

    # Write data rows
    for log in logs.order_by('-request_timestamp'):
        writer.writerow([
            log.user.get_full_name(),
            log.location.name,
            log.get_status_display(),
            log.request_timestamp.strftime('%Y-%m-%d %H:%M'),
            log.entry_timestamp.strftime('%Y-%m-%d %H:%M') if log.entry_timestamp else 'N/A',
            log.exit_timestamp.strftime('%Y-%m-%d %H:%M') if log.exit_timestamp else 'N/A',
            log.notes,
            log.group_members,
            log.activity_report,
            log.get_outcome_display()
        ])

    return response