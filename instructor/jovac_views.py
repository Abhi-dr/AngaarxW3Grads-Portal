from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.db.models import Q
from accounts.models import Administrator, Student, Instructor
from student.models import Notification, Anonymous_Message, Feedback, Assignment, AssignmentSubmission, Course, CourseRegistration, CourseSheet

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

    course_sheets = CourseSheet.objects.filter(course = course)

    parameters = {
        "course": course,
        "instructors": instructors,
        "course_sheets": course_sheets,
        # "assignments": assignments,
    }

    return render(request, "instructor/jovac/course.html", parameters)


# ======================================== JOVAC SHEETS ======================================

def jovac_sheet(request, course_slug, sheet_slug):
    course = get_object_or_404(Course, slug=course_slug)
    instructors = course.instructors.all()
    course_ct = ContentType.objects.get_for_model(Course)

    course_sheet = CourseSheet.objects.get(course = course, slug=sheet_slug)

    assignments = course_sheet.get_ordered_assignments()

    print(assignments)

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
        "sheet": course_sheet,
        "instructors": instructors,
        "assignments": assignments,
    }

    return render(request, "instructor/jovac/course_sheet.html", parameters)


# ======================================= ADD COURSE SHEET ==================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_sheet(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        thumbnail = request.FILES.get('thumbnail')
        created_by = request.user.instructor if hasattr(request.user, 'instructor') else None

        sheet = CourseSheet.objects.create(
            name=name,
            description=description,
            thumbnail=thumbnail,
            created_by=created_by,
        )
        sheet.course.add(course)

        messages.success(request, "Sheet created successfully.")
        return redirect('instructor_jovac', slug=course.slug)

    return render(request, 'instructor/jovac/add_sheet.html', {'course': course})

# ======================================= EDIT COURSE SHEET ===============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def edit_sheet(request, course_slug, sheet_slug):
    course = get_object_or_404(Course, slug=course_slug)
    sheet = get_object_or_404(CourseSheet, slug=sheet_slug, course=course)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_enabled = bool(request.POST.get('is_enabled'))
        is_approved = bool(request.POST.get('is_approved'))
        thumbnail = request.FILES.get('thumbnail')

        sheet.name = name
        sheet.description = description
        sheet.is_enabled = is_enabled
        sheet.is_approved = is_approved

        if thumbnail:
            sheet.thumbnail = thumbnail

        sheet.save()

        messages.success(request, "Sheet updated successfully.")
        return redirect('instructor_jovac', slug=course.slug)

    context = {
        'course': course,
        'sheet': sheet,
    }
    return render(request, 'instructor/jovac/edit_sheet.html', context)


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


# ============================= APPROVE ENROLLMENT REQUEST =============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def approve_enrollment_request(request, id):
    registration = get_object_or_404(CourseRegistration, id=id)
    
    # Update the registration status and save it
    registration.status = 'Approved'
    registration.save()

    return redirect(reverse('instructor_jovac_enrollment_requests', args=[registration.course.slug]))




# ================================================================================================
# ========================================= ASSIGNMENTS WORK =====================================
# ================================================================================================

# ======================================== ADD ASSIGNMENT ========================================

# ======================================== ADD ASSIGNMENT ========================================
@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_assignment(request, course_slug, sheet_slug):
    # Get Course and Sheet
    course = get_object_or_404(Course, slug=course_slug)
    course_content_type = ContentType.objects.get_for_model(course)
    course_sheet = get_object_or_404(CourseSheet, slug=sheet_slug, course=course)

    if request.method == 'POST':
        title = request.POST.get('title')
        is_tutorial = request.POST.get('is_tutorial') == 'on'

        # Shared fields for both
        assignment_data = {
            'content_type': course_content_type,
            'object_id': course.id,
            'title': title,
            'is_tutorial': is_tutorial,
        }

        if is_tutorial:
            # For tutorials: use only content field
            content = request.POST.get('content')
            tutorial_link = request.POST.get('tutorial_link', '').strip()
            assignment_data['content'] = content
            assignment_data['tutorial_link'] = tutorial_link
        else:
            # For regular assignments
            description = request.POST.get('description')
            due_date = request.POST.get('due_date')
            assignment_type = request.POST.get('assignment_type')
            max_score = request.POST.get('max_score')
            evaluation_script = request.FILES.get('evaluation_script')
            status = request.POST.get('status')
            instructions = request.POST.get('instructions')
            allow_late = bool(request.POST.get('allow_late_submission'))
            late_penalty = request.POST.get('late_penalty_per_day') or 0

            assignment_data.update({
                'description': description,
                'assignment_type': assignment_type,
                'max_score': max_score,
                "evaluation_script": evaluation_script,
                'status': status,
                'instructions': instructions,
                'allow_late_submission': allow_late,
                'late_penalty_per_day': late_penalty,
            })

        # Save assignment
        assignment = Assignment.objects.create(**assignment_data)
        assignment.course_sheets.add(course_sheet)

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

# ======================================== REORDER ASSIGNMENTS ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def reorder_assignments(request, slug):
    course_sheet = get_object_or_404(CourseSheet, slug=slug)
    assignments = course_sheet.get_ordered_assignments()

    return render(request, 'instructor/jovac/reorder.html', {
        "course_sheet": course_sheet,
        "assignments": assignments
    })


def update_assignment_order(request, id):
    course_sheet = get_object_or_404(CourseSheet, id=id)
    order = request.POST.getlist("order[]")  # JS will send order[]=1&order[]=2

    try:
        new_order = {str(assignment_id): index for index, assignment_id in enumerate(order)}
        course_sheet.custom_order = new_order
        course_sheet.save()
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
