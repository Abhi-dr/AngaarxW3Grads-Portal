from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from accounts.models import Student, Instructor
from student.models import Notification, Anonymous_Message
from practice.models import POD, Submission, Question, Sheet, Batch,EnrollmentRequest

import datetime


# ========================= BATCH WORK ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def batches(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    batches = Batch.objects.all()
    
    parameters = {
        "instructor": instructor,
        "batches": batches
        
    }
    
    return render(request, 'administration/batch/batches.html', parameters)


# =================================== ADD BATCH ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_batch(request):
    
    instructor = Instructor.objects.get(id=request.user.id)

    
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
        return redirect('instructor_batches')
        
    parameters = {
        "instructor": instructor
    }
    
    return render(request, 'administration/batch/add_batch.html', parameters)


# =============================== ENROLLMENT REQUESTS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def enrollment_requests(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    total_pending_requests = EnrollmentRequest.objects.filter(status="Pending").count()
    
    
    parameters = {
        "instructor": instructor,
        "total_pending_requests": total_pending_requests
    }
    
    return render(request, "administration/batch/students_enroll_request.html", parameters)

# =============================== FETCH PENDING ENROLLMENT REQUESTS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def fetch_pending_enrollments(request):

    enrollment_requests = EnrollmentRequest.objects.select_related('student', 'batch').filter(status="Pending").order_by('-request_date')

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


# ================================== FETCH REJECTED ENROLLMENT REQUESTS ==================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
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
def approve_enrollment(request, id):
    
    enrollment_request = EnrollmentRequest.objects.get(id=id)
    enrollment_request.status = "Accepted"
    enrollment_request.save()
    
    messages.success(request, "Enrollment request accepted")
    return redirect('instructor_enrollment_requests')

# =============================== REJECT ENROLLMENT REQUESTS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def reject_enrollment(request, id):
    
    enrollment_request = EnrollmentRequest.objects.get(id=id)
    enrollment_request.status = "Rejected"
    enrollment_request.save()
    
    messages.success(request, "Enrollment request rejected")
    return redirect('instructor_enrollment_requests')


# =============================== BATCH DETAILS ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def batch(request, slug):
    
    instructor = Instructor.objects.get(id=request.user.id)
    batch = Batch.objects.get(slug=slug)
    
        
    try:
        pod = POD.objects.get(batch=batch, date=datetime.date.today())
    except POD.DoesNotExist:
        pod = None
    

    parameters = {
        "instructor": instructor,
        "batch": batch,
        "pod": pod
    }
    
    return render(request, 'administration/batch/batch.html', parameters)

# =============================== SET POD FOR BATCH ==============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def instructor_set_pod_for_batch(request, slug):
    
    batch = get_object_or_404(Batch, slug=slug)
    
    # Fetch the instructor and questions without existing PODs
    instructor = Instructor.objects.get(id=request.user.id)
    questions = Question.objects.filter(pods__isnull=True)
    
    # check if pod for that day is already set
    pod = POD.objects.filter(batch=batch, date=datetime.date.today())
    
    
    if pod:
        messages.warning(request, f"POD for today is already set for batch '{batch.name}'.")
        return redirect('instructor_batch' , slug=slug)
    
    if request.method == "POST":
        question_id = request.POST.get("question_id")
        
        if question_id:
            question = get_object_or_404(Question, id=question_id)
            
            # Create or update the POD for this batch
            pod, created = POD.objects.get_or_create(question=question, batch=batch)
            
            if created:
                messages.success(request, f"POD set successfully for batch '{batch.name}'.")
            else:
                messages.warning(request, "This question is already set as POD for this batch.")
            return redirect('instructor_set_pod_for_batch', slug=slug)
        else:
            messages.error(request, "Please select a valid question.")
    
    parameters = {
        "instructor": instructor,
        "questions": questions,
        "batch": batch,
        "pod": pod
    }
    
    return render(request, 'administration/batch/set_pod.html', parameters)


