from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.timezone import now

from accounts.models import Student, Administrator
from practice.models import POD, Submission, Question, Sheet, Batch,EnrollmentRequest
from django.db.models import Subquery, OuterRef
from angaar_hai.custom_decorators import admin_required


import datetime



# ========================= BATCH WORK ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def batches(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    batches = Batch.objects.all()
    
    parameters = {
        "administrator": administrator,
        "batches": batches
        
    }
    
    return render(request, 'administration/batch/batches.html', parameters)


# =================================== ADD BATCH ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def add_batch(request):
    
    administrator = Administrator.objects.get(id=request.user.id)

    
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        thumbnail = request.FILES.get('thumbnail')
        
        batch = Batch.objects.create(
            name=name,
            description=description,
            thumbnail=thumbnail
        )
        
        batch.save()
        
        messages.success(request, "Course added successfully")
        return redirect('administrator_batches')
        
    parameters = {
        "administrator": administrator
    }
    
    return render(request, 'administration/batch/add_batch.html', parameters)


# =============================== ENROLLMENT REQUESTS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def enrollment_requests(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    total_pending_requests = EnrollmentRequest.objects.filter(status="Pending").count()
    
    parameters = {
        "administrator": administrator,
        "total_pending_requests": total_pending_requests
    }
    
    return render(request, "administration/batch/students_enroll_request.html", parameters)

# ================================ APPROVE ALL ENROLLMENT REQUESTS ====================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def approve_all_enrollments(request):
    enrollment_requests = EnrollmentRequest.objects.filter(status="Pending")
    for request in enrollment_requests:
        request.status = "Accepted"
        request.save()
        
    messages.success(request, "All pending enrollment requests have been accepted.")
    return redirect('administrator_enrollment_requests')

# =============================== FETCH PENDING ENROLLMENT REQUESTS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def fetch_pending_enrollments(request):

    enrollment_requests = EnrollmentRequest.objects.select_related('student', 'batch').filter(status="Pending").order_by('-request_date')

        # Format the data for JSON response
    data = []
    for request_obj in enrollment_requests:
        data.append({
            'id': request_obj.id,
            'student_name': request_obj.student.first_name + " " + request_obj.student.last_name,
            'batch_name': request_obj.batch.name,
            'status': request_obj.status,
            "status_color": "success" if request_obj.status == "Accepted" else "danger",
            'request_date': request_obj.request_date.strftime('%d %b, %Y'),
        })

    # Return the data as a JSON response
    return JsonResponse({'success': True, 'data': data}, status=200)


# ================================== FETCH REJECTED ENROLLMENT REQUESTS ==================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def fetch_rejected_enrollments(request):
    
    enrollment_requests = EnrollmentRequest.objects.select_related('student', 'batch').filter(status="Rejected").order_by('-request_date')

    # Format the data for JSON response
    data = []
    for request_obj in enrollment_requests:
        data.append({
            'id': request_obj.id,
            'student_name': request_obj.student.first_name + request_obj.student.last_name,
            'batch_name': request_obj.batch.name,
            'status': request_obj.status,
            "status_color": "success" if request_obj.status == "Accepted" else "danger",
            'request_date': request_obj.request_date.strftime('%d %b, %Y'),
        })

    # Return the data as a JSON response
    return JsonResponse({'success': True, 'data': data}, status=200)

# =============================== ACCEPT ENROLLMENT REQUESTS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def approve_enrollment(request, id):
    
    enrollment_request = EnrollmentRequest.objects.get(id=id)
    enrollment_request.status = "Accepted"
    enrollment_request.save()
    
    messages.success(request, "Enrollment request accepted")
    return redirect('administrator_enrollment_requests')

# =============================== REJECT ENROLLMENT REQUESTS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def reject_enrollment(request, id):
    
    enrollment_request = EnrollmentRequest.objects.get(id=id)
    enrollment_request.status = "Rejected"
    enrollment_request.save()
    
    messages.success(request, "Enrollment request rejected")
    return redirect('administrator_enrollment_requests')


# =============================== BATCH DETAILS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def batch(request, slug):
    
    administrator = Administrator.objects.get(id=request.user.id)
    batch = Batch.objects.get(slug=slug)
    
    # Fetch all the sheets for this batch
    sheets = batch.sheets.all().order_by("-id")
        
    try:
        pod = POD.objects.get(batch=batch, date=datetime.date.today())
    except POD.DoesNotExist:
        pod = None
    

    parameters = {
        "administrator": administrator,
        "batch": batch,
        "sheets": sheets,
        "pod": pod
    }
    
    return render(request, 'administration/batch/batch.html', parameters)

# =============================== SET POD FOR BATCH ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def administrator_set_pod_for_batch(request, slug):
    batch = get_object_or_404(Batch, slug=slug)

    # Fetch the administrator and questions without existing PODs for the selected batch
    administrator = Administrator.objects.get(id=request.user.id)
    questions = Question.objects.filter(pods__batch__isnull=True)

    # Fetch existing PODs for the batch
    today_pod = POD.objects.filter(batch=batch, date=datetime.datetime.today().date())
    past_pods = POD.objects.filter(batch=batch).order_by('-date').exclude(date__gt=datetime.datetime.today().date())
    upcoming_pods = POD.objects.filter(batch=batch, date__gt=datetime.datetime.today().date()).order_by('date')

    if request.method == "POST":
        question_id = request.POST.get("question_id")
        pod_date = request.POST.get("pod_date")  # Fetch the date from the form
        
        if question_id and pod_date:
            try:
                pod_date = datetime.datetime.strptime(pod_date, "%Y-%m-%d").date()  # Parse the date
                
                if pod_date < now().date():
                    messages.error(request, "You cannot set a POD for a past date.")
                    return redirect('administrator_set_pod_for_batch', slug=slug)
                
                if pod_date == now().date() and today_pod.exists():
                    messages.warning(request, f"POD for today is already set for batch '{batch.name}'.")
                    return redirect('administrator_set_pod_for_batch', slug=slug)
                
                else:
                    question = get_object_or_404(Question, id=question_id)
                    
                    # Check if a POD already exists for this batch and date
                    today_pod = POD.objects.create(
                        question=question, 
                        batch=batch, 
                        date=pod_date
                    )
                    
                    today_pod.save()
                    
                    messages.success(request, f"POD set successfully for batch '{batch.name}'")
                    return redirect('administrator_set_pod_for_batch', slug=slug)
                
            except ValueError:
                messages.error(request, "Invalid date format. Please select a valid date.")
        else:
            messages.error(request, "Please select a valid question and date.")

    parameters = {
        "administrator": administrator,
        "questions": questions,
        "batch": batch,
        "pod": today_pod,
        "past_pods": past_pods,
        "upcoming_pods": upcoming_pods,
        "default_date": now().date().isoformat(),  # Set default date for the form
    }

    return render(request, 'administration/batch/set_pod.html', parameters)



# =============================== VIEW SUBMISSIONS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def view_submissions(request, slug):
    
    question = get_object_or_404(Question, slug=slug)
    administrator = Administrator.objects.get(id=request.user.id)
    # submissions = Submission.objects.filter(question=question, status="Accepted").distinct().order_by('-submitted_at')
    
    latest_submission_time = Submission.objects.filter(
        question=question, 
        user=OuterRef('user'), 
        status="Accepted"
    ).order_by('-submitted_at').values('submitted_at')[:1]

    # Filter submissions to include only the latest submission per student
    latest_submissions = Submission.objects.filter(
        question=question, 
        status="Accepted", 
        submitted_at=Subquery(latest_submission_time)
    )
    
    parameters = {
        "question": question,
        "submissions": latest_submissions,
        "administrator": administrator
    }
    
    return render(request, 'administration/batch/view_submissions.html', parameters)

# ================================= BATCH ENROLLMENT REQUESTS ==================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def batch_enrollment_requests(request, slug):
    
    administrator = Administrator.objects.get(id=request.user.id)
    batch = Batch.objects.get(slug=slug)
    total_pending_requests = EnrollmentRequest.objects.filter(batch=batch, status="Pending").count()
    
    parameters = {
        "administrator": administrator,
        "batch": batch,
        "total_pending_requests": total_pending_requests
    }
    
    return render(request, "administration/batch/batch_enrollment_requests.html", parameters)

# =============================== FETCH PENDING ENROLLMENT REQUESTS OF BATCH ===================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def fetch_pending_enrollments_of_batch(request, slug):
    
    batch = Batch.objects.get(slug=slug)
    enrollment_requests = EnrollmentRequest.objects.select_related('student', 'batch').filter(batch=batch, status="Pending").order_by('-request_date')

    # Format the data for JSON response
    data = []
    for request_obj in enrollment_requests:
        data.append({
            'id': request_obj.id,
            'student_name': request_obj.student.first_name + " " + request_obj.student.last_name,
            'status': request_obj.status,
            "status_color": "success" if request_obj.status == "Accepted" else "danger",
            'request_date': request_obj.request_date.strftime('%d %b, %Y'),
        })

    # Return the data as a JSON response
    return JsonResponse({'success': True, 'data': data}, status=200)

# =============================== FETCH REJECTED ENROLLMENT REQUESTS OF BATCH ===================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def fetch_rejected_enrollments_of_batch(request, slug):
    
    batch = Batch.objects.get(slug=slug)
    enrollment_requests = EnrollmentRequest.objects.select_related('student', 'batch').filter(batch=batch, status="Rejected").order_by('-request_date')

    # Format the data for JSON response
    data = []
    for request_obj in enrollment_requests:
        data.append({
            'id': request_obj.id,
            'student_name': request_obj.student.first_name + " " + request_obj.student.last_name,
            'status': request_obj.status,
            "status_color": "success" if request_obj.status == "Accepted" else "danger",
            'request_date': request_obj.request_date.strftime('%d %b, %Y'),
        })

    # Return the data as a JSON response
    return JsonResponse({'success': True, 'data': data}, status=200)

# =============================== ACCEPT ENROLLMENT REQUESTS OF BATCH ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def approve_enrollment_batch(request, id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # Check if the request is AJAX
        try:
            enrollment_request = EnrollmentRequest.objects.get(id=id)
            enrollment_request.status = "Accepted"
            enrollment_request.save()
            return JsonResponse({
                'success': True,
                'message': 'Enrollment request accepted',
                'id': id
            })
        except EnrollmentRequest.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Enrollment request not found'
            }, status=404)
    else:
        messages.success(request, "Enrollment request accepted")
        return redirect('administrator_batch_enrollment_requests', slug=enrollment_request.batch.slug)


# =============================== REJECT ENROLLMENT REQUESTS OF BATCH ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def reject_enrollment_batch(request, id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            enrollment_request = EnrollmentRequest.objects.get(id=id)
            enrollment_request.status = "Rejected"
            enrollment_request.save()
            return JsonResponse({
                'success': True,
                'message': 'Enrollment request rejected',
                'id': id
            })
        except EnrollmentRequest.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Enrollment request not found'
            }, status=404)
    else:
        messages.success(request, "Enrollment request rejected")
        return redirect('administrator_batch_enrollment_requests', slug=enrollment_request.batch.slug)