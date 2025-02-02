from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Student, Administrator
from practice.models import POD, Submission, Question, Sheet, Batch,EnrollmentRequest
from django.db.models import Subquery, OuterRef
from angaar_hai.custom_decorators import admin_required


import datetime

# ========================= INSTRUCTOR BATCH WORK ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def batches(request):
    
    batches = Batch.objects.all()
    
    parameters = {
        "batches": batches        
    }
    
    return render(request, 'instructor/batch/batches.html', parameters)


# =============================== BATCH DETAILS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def batch(request, slug):
    
    batch = Batch.objects.get(slug=slug)
    
    # Fetch all the sheets for this batch
    sheets = batch.sheets.all().order_by("-id")
        
    try:
        pod = POD.objects.get(batch=batch, date=datetime.date.today())
    except POD.DoesNotExist:
        pod = None
    

    parameters = {
        "batch": batch,
        "sheets": sheets,
        "pod": pod
    }
    
    return render(request, 'instructor/batch/batch.html', parameters)


# =============================== SET POD FOR BATCH ==============================


@login_required(login_url='login')
@staff_member_required(login_url='login')
def set_pod_for_batch(request, slug):
    batch = get_object_or_404(Batch, slug=slug)

    # Fetch existing PODs for the batch
    
    pods = POD.objects.select_related('question').filter(batch=batch)
    
    today_pod = pods.filter(date=datetime.datetime.today().date())
    past_pods = pods.order_by('-date').exclude(date__gt=datetime.datetime.today().date())
    upcoming_pods = pods.filter(date__gt=datetime.datetime.today().date()).order_by('date')

    parameters = {
        "batch": batch,
        "pod": today_pod,
        "past_pods": past_pods,
        "upcoming_pods": upcoming_pods,
        "default_date": now().date().isoformat(),  # Set default date for the form
    }

    return render(request, 'instructor/batch/set_pod.html', parameters)

# =============================== VIEW SUBMISSIONS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def view_submissions(request, slug):
    question = get_object_or_404(Question, slug=slug)
    
    parameters = {
        "question": question,
    }
    
    return render(request, 'instructor/batch/view_submissions.html', parameters)
