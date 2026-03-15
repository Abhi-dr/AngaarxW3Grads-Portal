from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from angaar_hai.custom_decorators import admin_required
from student.event_models import Event, CertificateTemplate, Certificate


@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def events(request):
    """Render the Events list page (SPA — data fetched via DRF)."""
    return render(request, 'administration/events/index.html')


@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def event_detail(request, pk):
    """Render the Event detail + certificate management page."""
    event = get_object_or_404(Event, pk=pk)
    return render(request, 'administration/events/event_detail.html', {'event': event})

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def certificate_templates(request):
    """Render the Certificate Templates management page."""
    return render(request, 'administration/events/templates.html')

