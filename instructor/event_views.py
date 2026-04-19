from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden

from student.event_models import Event


@login_required(login_url='login')
@staff_member_required(login_url='login')
def events(request):
    if not getattr(request.user, 'is_submission', False):
        return HttpResponseForbidden('Not allowed')
    return render(request, 'instructor/events/index.html')


@login_required(login_url='login')
@staff_member_required(login_url='login')
def event_detail(request, pk):
    if not getattr(request.user, 'is_submission', False):
        return HttpResponseForbidden('Not allowed')
    event = get_object_or_404(Event, pk=pk)
    return render(request, 'instructor/events/event_detail.html', {'event': event})


@login_required(login_url='login')
@staff_member_required(login_url='login')
def certificate_templates(request):
    if not getattr(request.user, 'is_submission', False):
        return HttpResponseForbidden('Not allowed')
    return render(request, 'instructor/events/templates.html')
