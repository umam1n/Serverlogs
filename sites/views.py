from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ServerLocation

@login_required
def site_list(request):
    sites = ServerLocation.objects.all()
    for site in sites:
        # Find the active log by looking for a 'Checked-In' status
        site.active_log = site.serverroomaccesslog_set.filter(status='Checked-In').first()
    return render(request, 'sites/list.html', {'sites': sites})