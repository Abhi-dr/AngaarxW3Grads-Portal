from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from datetime import timedelta

from accounts.models import CustomUser
from student.models import Notification
from practice.models import POD, Submission, Question, Sheet, Batch,EnrollmentRequest
from django.db.models import Subquery, OuterRef
from angaar_hai.custom_decorators import admin_required


import datetime

# ========================= INSTRUCTOR BATCH WORK ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def batches(request):
    batches = Batch.objects.order_by("-id")

    parameters = {
        "batches": batches,
    }

    return render(request, 'instructor/batch/batches.html', parameters)


@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_batch_request(request):
    if request.method == "POST":
        name = (request.POST.get('name') or '').strip()
        description = (request.POST.get('description') or '').strip()
        thumbnail = request.FILES.get('thumbnail')

        if not name:
            messages.error(request, "Course name is required.")
            return render(request, 'instructor/batch/add_batch_request.html')

        if Batch.objects.filter(name__iexact=name).exists():
            messages.error(request, "A course with this name already exists.")
            return render(request, 'instructor/batch/add_batch_request.html')

        batch = Batch.objects.create(
            name=name,
            description=description,
            thumbnail=thumbnail,
            is_active=False,
        )

        reviewer_url = reverse('administrator_batches')
        requester = request.user.get_full_name() or request.user.email
        Notification.objects.create(
            title='Approval Request: Course',
            description=f"{requester} created Course '{batch.name}' and requested admin approval. Review: {reviewer_url}",
            is_alert=True,
            is_fixed=False,
            type='warning',
            expiration_date=now() + timedelta(days=30),
        )

        messages.success(request, "Course request sent to admin for approval.")
        return redirect('instructor_batches')

    return redirect('instructor_batches')


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


@login_required(login_url='login')
@staff_member_required(login_url='login')
def batch_sheet(request, batch_slug, sheet_slug):
    batch = get_object_or_404(Batch, slug=batch_slug)
    sheet = get_object_or_404(Sheet, slug=sheet_slug, batches=batch)
    questions = sheet.get_ordered_questions()

    parameters = {
        "batch": batch,
        "sheet": sheet,
        "questions": questions,
        "from_course": True,
        "course_slug": batch.slug,
        "return_url": request.path,
    }

    return render(request, 'instructor/sheet/sheet.html', parameters)


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

# ================================= BATCH ENROLLMENT REQUESTS ==================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def batch_enrollment_requests(request, slug):
    
    batch = Batch.objects.get(slug=slug)
    total_pending_requests = EnrollmentRequest.objects.filter(batch=batch, status="Pending").count()
    
    parameters = {
        "batch": batch,
        "total_pending_requests": total_pending_requests
    }
    
    return render(request, "instructor/batch/batch_enrollment_requests.html", parameters)
