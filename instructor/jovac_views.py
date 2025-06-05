from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.db.models import Q
from accounts.models import Administrator, Student, Instructor
from student.models import Notification, Anonymous_Message, Feedback, Assignment, AssignmentSubmission, Course, CourseRegistration

from django.contrib.contenttypes.models import ContentType

from practice.models import Sheet, Submission, Question
from home.models import FlamesRegistration, FlamesCourse
from angaar_hai.custom_decorators import admin_required
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
from django.utils import timezone
import datetime
from django.http import JsonResponse
import math


from django.utils.timezone import now
from datetime import timedelta

from practice.models import Streak

# ======================================== MY JOVAC COURSE ======================================

def jovacs(request):
    instructor = get_object_or_404(Instructor, id=request.user.id)

    # Get only courses where the logged-in instructor is assigned
    courses = Course.objects.filter(instructors=instructor, is_active=True)

    parameters = {
        "courses": courses,
    }

    return render(request, "instructor/jovac/jovacs.html", parameters)


# ======================================== MY JOVAC COURSE ======================================

def jovac(request, slug):
    course = get_object_or_404(Course, slug=slug)
    instructors = course.instructors.all()
    course_ct = ContentType.objects.get_for_model(Course)

    assignments = Assignment.objects.filter(
        content_type=course_ct,
        object_id=course.id
    )

    query = request.POST.get("query")
    if query:
        assignments = Assignment.objects.filter(
            Q(id__icontains=query) |
            Q(title__icontains=query) |
            Q(description__icontains=query)|
            Q(assignment_type__icontains=query)
            )


    parameters = {
        "course": course,
        "instructors": instructors,
        "assignments": assignments,
        "query": query
    }

    return render(request, "instructor/jovac/course.html", parameters)

# ========================================= Enrollment Requests =============================

def enrollment_requests(request, slug):
    course = get_object_or_404(Course, slug=slug)
    pending_requests = CourseRegistration.objects.filter(course=course, status='pending')

    parameters = {
        "course": course,
        "pending_requests": pending_requests,
        "total_pending_requests": pending_requests.count(),
    }

    return render(request, 'instructor/jovac/enrollment_requests.html', parameters)


# ================================================================================================
# ========================================= ASSIGNMENTS WORK =====================================
# ================================================================================================

# ======================================== ADD ASSIGNMENT ========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_assignment(request, slug):
    # Get the course object and its content type
    course = get_object_or_404(Course, slug=slug)
    course_content_type = ContentType.objects.get_for_model(course)

    print(course)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        assignment_type = request.POST.get('assignment_type')
        due_date = request.POST.get('due_date')
        max_score = request.POST.get('max_score')
        status = request.POST.get('status')
        instructions = request.POST.get('instructions')
        allow_late = bool(request.POST.get('allow_late_submission'))
        late_penalty = request.POST.get('late_penalty_per_day') or 0

        assignment = Assignment.objects.create(
            content_type=course_content_type,
            object_id=course.id,
            title=title,
            description=description,
            assignment_type=assignment_type,
            due_date=due_date,
            max_score=max_score,
            status=status,
            instructions=instructions,
            allow_late_submission=allow_late,
            late_penalty_per_day=late_penalty
        )

        assignment.save()

        messages.success(request, "Assignment added successfully.")
        return redirect('instructor_jovac', slug=course.slug)

    context = {
        'course': course,
        'assignment_types': Assignment.ASSIGNMENT_TYPES,
        'status_choices': Assignment.STATUS_CHOICES
    }
    return render(request, 'instructor/jovac/add_assignment.html', context)

# ======================================== EDIT ASSIGNMENT ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def edit_assignment(request, id):
    assignment = get_object_or_404(Assignment, id=id)
    course = assignment.course

    if request.method == "POST":
        title = request.POST.get('title')
        description = request.POST.get('description')
        assignment_type = request.POST.get('assignment_type')
        due_date = request.POST.get('due_date')
        max_score = request.POST.get('max_score')
        status = request.POST.get('status')
        instructions = request.POST.get('instructions')
        allow_late_submission = bool(request.POST.get('allow_late_submission'))
        late_penalty = request.POST.get('late_penalty_per_day') or 0

        assignment.title = title
        assignment.description = description
        assignment.assignment_type = assignment_type
        assignment.due_date = due_date
        assignment.max_score = max_score
        assignment.status = status
        assignment.instructions = instructions
        assignment.allow_late_submission = allow_late_submission
        assignment.late_penalty_per_day = late_penalty

        try:
            assignment.full_clean()
            assignment.save()
            messages.success(request, "Assignment updated successfully!")
            return redirect('instructor_jovac', course.slug)
        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, 'instructor/jovac/edit_assignment.html', {
        'assignment': assignment,
        'course': course,
        'assignment_types': Assignment.ASSIGNMENT_TYPES,
        'status_choices': Assignment.STATUS_CHOICES,
    })


# ======================================== VIEW SUBMISSIONS ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def view_submissions(request, id):
            
    assignment = Assignment.objects.get(id=id)
    
    submissions = AssignmentSubmission.objects.filter(assignment=assignment)
        
    query = request.POST.get("query")
    if query:
        submissions = AssignmentSubmission.objects.filter(
            Q(id__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query)
            )
    
    parameters = {
        "assignment": assignment,
        "submissions": submissions,
        "query": query
    }
    
    return render(request, "instructor/jovac/submissions.html", parameters)