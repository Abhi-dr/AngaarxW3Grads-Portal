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

