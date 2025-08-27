from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import csv
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Count, F, Avg, ExpressionWrapper, DurationField, Q
from django.db.models.functions import TruncDay
from logs.models import ServerRoomAccessLog, ActivityCategory
from sites.models import ServerLocation

@login_required
def dashboard_view(request):
    # --- Filtering Logic ---
    time_filter = request.GET.get('time_filter', 'all')
    end_date = timezone.now()
    start_date = None
    if time_filter == 'day':
        start_date = end_date - timedelta(days=1)
    elif time_filter == 'week':
        start_date = end_date - timedelta(weeks=1)
    elif time_filter == 'month':
        start_date = end_date - timedelta(days=30)

    status_filter = request.GET.get('status', '')
    site_filter = request.GET.get('site', '')
    category_filter = request.GET.get('category', '')
    user_search = request.GET.get('user_search', '')

    logs_query = ServerRoomAccessLog.objects.select_related('user', 'location', 'category').all()

    if start_date:
        logs_query = logs_query.filter(request_timestamp__gte=start_date)
    if status_filter:
        logs_query = logs_query.filter(status=status_filter)
    if site_filter:
        logs_query = logs_query.filter(location__id=site_filter)
    if category_filter:
        logs_query = logs_query.filter(category__id=category_filter)
    if user_search:
        logs_query = logs_query.filter(
            Q(user__first_name__icontains=user_search) |
            Q(user__last_name__icontains=user_search) |
            Q(user__username__icontains=user_search)
        )

    # --- Pagination Logic ---
    per_page = request.GET.get('per_page', '20') # Default to 20
    paginator = Paginator(logs_query.order_by('-request_timestamp'), per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- Data for Stats and Charts ---
    all_logs_count = paginator.count
    checked_in_count = logs_query.filter(status='Checked-In').count()
    completed_count = logs_query.filter(status='Completed').count()
    denied_count = logs_query.filter(status='Denied').count()
    visits_by_site = list(logs_query.values('location__name').annotate(count=Count('id')).order_by('-count'))
    visits_by_category = list(logs_query.values('category__name').annotate(count=Count('id')).order_by('-count'))
    sites_for_map = ServerLocation.objects.exclude(latitude__isnull=True, longitude__isnull=True)
    
    context = {
        'page_obj': page_obj,
        'all_sites': ServerLocation.objects.all(),
        'all_categories': ActivityCategory.objects.all(),
        'all_logs_count': all_logs_count,
        'checked_in_count': checked_in_count,
        'completed_count': completed_count,
        'denied_count': denied_count,
        'visits_by_site_data': visits_by_site,
        'visits_by_category_data': visits_by_category,
        'sites_json': [{'name': site.name, 'lat': site.latitude, 'lon': site.longitude} for site in sites_for_map],
        'site_filter': site_filter,
        'status_filter': status_filter,
        'time_filter': time_filter,
        'category_filter': category_filter,
        'user_search': user_search,
        'per_page': per_page,
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def export_logs_csv(request):
    # Filtering logic is the same as the dashboard view
    time_filter = request.GET.get('time_filter', 'all')
    end_date = timezone.now()
    start_date = None
    if time_filter == 'day':
        start_date = end_date - timedelta(days=1)
    elif time_filter == 'week':
        start_date = end_date - timedelta(weeks=1)
    elif time_filter == 'month':
        start_date = end_date - timedelta(days=30)

    status_filter = request.GET.get('status', '')
    site_filter = request.GET.get('site', '')
    # ... Add any other filters you want for the export, e.g., category, user_search ...

    logs = ServerRoomAccessLog.objects.select_related('user', 'location').all()
    if start_date:
        logs = logs.filter(request_timestamp__gte=start_date)
    if status_filter:
        logs = logs.filter(status=status_filter)
    if site_filter:
        logs = logs.filter(location__id=site_filter)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="server_room_logs.csv"'
    writer = csv.writer(response)
    writer.writerow(['User', 'Site', 'Status', 'Date Requested', 'Date In', 'Date Out', 'Purpose', 'Group Members', 'Activity Report', 'Outcome'])
    
    for log in logs.order_by('-request_timestamp'):
        writer.writerow([
            log.user.get_full_name(),
            log.location.name,
            log.get_status_display(),
            log.request_timestamp.strftime('%Y-%m-%d %H:%M'),
            log.entry_timestamp.strftime('%Y-%m-%d %H:%M') if log.entry_timestamp else 'N/A',
            log.exit_timestamp.strftime('%Y-%m-%d %H:%M') if log.exit_timestamp else 'N/A',
            log.notes,
            log.group_members.replace('\n', ', '),
            log.activity_report,
            log.get_outcome_display()
        ])
    return response

@login_required
def site_monitoring_view(request):
    if not request.user.is_staff:
        raise PermissionDenied

    managed_sites = ServerLocation.objects.filter(pics=request.user)
    if not managed_sites.exists():
        return render(request, 'dashboard/not_a_pic.html')

    site = managed_sites.first()
    all_site_logs = ServerRoomAccessLog.objects.filter(location=site)

    # --- Define the 90-day time window ---
    ninety_days_ago = timezone.now() - timedelta(days=90)
    recent_logs_for_metrics = all_site_logs.filter(request_timestamp__gte=ninety_days_ago)

    # --- Calculate Metrics ---

    # 1. Days since last access (uses all logs to find the most recent one)
    last_log = all_site_logs.filter(status='Completed', exit_timestamp__isnull=False).order_by('-exit_timestamp').first()
    days_since_last_access = (timezone.now() - last_log.exit_timestamp).days if last_log else 'N/A'

    # 2. Average visit duration (uses last 90 days)
    completed_logs = recent_logs_for_metrics.filter(status='Completed', entry_timestamp__isnull=False, exit_timestamp__isnull=False)
    duration_expression = ExpressionWrapper(F('exit_timestamp') - F('entry_timestamp'), output_field=DurationField())
    average_duration_data = completed_logs.aggregate(average_duration=Avg(duration_expression))
    average_duration = average_duration_data.get('average_duration')

    # 3. Most frequent visitor (uses last 90 days)
    top_visitor = (recent_logs_for_metrics
                   .values('user__first_name', 'user__last_name')
                   .annotate(visit_count=Count('user'))
                   .order_by('-visit_count').first())

    # --- Chart Data ---
    # 1. Visits per day (last 30 days - this can remain shorter for a clearer chart)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    visits_per_day = (all_site_logs.filter(request_timestamp__gte=thirty_days_ago)
                      .annotate(day=TruncDay('request_timestamp'))
                      .values('day')
                      .annotate(count=Count('id'))
                      .order_by('day'))

    # 2. Top 5 most common activities (uses last 90 days)
    top_activities = (recent_logs_for_metrics.filter(category__isnull=False)
                      .values('category__name')
                      .annotate(count=Count('category'))
                      .order_by('-count')[:5])

    # --- Pagination for the full log history ---
    paginator = Paginator(all_site_logs.order_by('-request_timestamp'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'site': site,
        'days_since_last_access': days_since_last_access,
        'average_duration': average_duration,
        'top_visitor': top_visitor,
        'page_obj': page_obj,
        'visits_per_day_data': list(visits_per_day),
        'top_activities_data': list(top_activities),
    }
    return render(request, 'dashboard/site_dashboard.html', context)