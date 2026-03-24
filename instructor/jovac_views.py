from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.db.models import Q
from accounts.models import CustomUser
from student.models import Notification, Anonymous_Message, Feedback, Assignment, AssignmentSubmission, Course, CourseRegistration, CourseSheet

from django.contrib.contenttypes.models import ContentType
from django.utils.dateparse import parse_datetime

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

from practice.models import Streak, MCQQuestion


def _notify_admin_approval_request(created_by, item_type, item_name, details_url=''):
    """Create a dashboard notification for admin approval requests from instructor side."""
    title = f"Approval Request: {item_type}"
    requester = created_by.get_full_name() or created_by.email
    description = f"{requester} created {item_type} '{item_name}' and requested admin approval."
    if details_url:
        description = f"{description} Review: {details_url}"

    Notification.objects.create(
        title=title,
        description=description,
        is_alert=True,
        is_fixed=False,
        type='warning',
        expiration_date=timezone.now() + timedelta(days=30),
    )

# ======================================== MY JOVAC COURSE ======================================

def jovacs(request):
    instructor = get_object_or_404(CustomUser, id=request.user.id)

    # Show both active and pending courses created/assigned for this instructor.
    courses = Course.objects.filter(instructors=instructor)

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

    items = course_sheet.get_ordered_items()

    query = request.POST.get("query")
    if query:
        needle = query.lower().strip()
        items = [
            item for item in items
            if needle in str(item.get('pk', '')).lower()
            or needle in (getattr(item['obj'], 'title', '') or '').lower()
            or needle in (getattr(item['obj'], 'question_text', '') or '').lower()
            or needle in (getattr(item['obj'], 'description', '') or '').lower()
            or needle in item.get('type', '').lower()
        ]


    parameters = {
        "course": course,
        "sheet": course_sheet,
        "instructors": instructors,
        "items": items,
        "query": query,
    }

    return render(request, "instructor/jovac/course_sheet.html", parameters)


@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_course(request):
    instructors = CustomUser.objects.filter(role='instructor')

    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        description = (request.POST.get('description') or '').strip()
        thumbnail = request.FILES.get('thumbnail')
        selected_instructors = request.POST.getlist('instructors')

        if not name or not description:
            messages.error(request, 'Course name and description are required.')
            return render(request, 'instructor/jovac/add_course.html', {'instructors': instructors})

        course = Course.objects.create(
            name=name,
            description=description,
            thumbnail=thumbnail,
            is_active=False,
        )

        if selected_instructors:
            course.instructors.set(selected_instructors)

        if request.user.id not in set(course.instructors.values_list('id', flat=True)):
            course.instructors.add(request.user)

        _notify_admin_approval_request(
            created_by=request.user,
            item_type='Course',
            item_name=course.name,
            details_url=reverse('administrator_batches'),
        )

        messages.success(request, 'Course created and sent for admin approval.')
        return redirect('instructor_jovacs')

    return render(request, 'instructor/jovac/add_course.html', {'instructors': instructors})


# ======================================= ADD COURSE SHEET ==================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_sheet(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        thumbnail = request.FILES.get('thumbnail')
        # created_by FK points to CustomUser — request.user IS the CustomUser (instructor)
        created_by = request.user

        sheet = CourseSheet.objects.create(
            name=name,
            description=description,
            thumbnail=thumbnail,
            created_by=created_by,
            is_enabled=False,
            is_approved=False,
        )
        sheet.course.add(course)

        _notify_admin_approval_request(
            created_by=request.user,
            item_type='Course Sheet',
            item_name=sheet.name,
            details_url=reverse('administrator_batches'),
        )

        messages.success(request, "Sheet created and sent for admin approval.")
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



# ================================================================================================
# ========================================= ASSIGNMENTS WORK =====================================
# ================================================================================================

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
            downloadable_file = request.FILES.get('downloadable_content')

            allow_late = bool(request.POST.get('allow_late_submission'))
            late_penalty = request.POST.get('late_penalty_per_day') or 0

            assignment_data.update({
                'description': description,
                'assignment_type': assignment_type,
                'max_score': max_score,
                "evaluation_script": evaluation_script,
                'status': status,
                'instructions': instructions,
                'downloadable_file': downloadable_file,
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
        is_tutorial = bool(request.POST.get('is_tutorial'))

        assignment.title = title
        assignment.is_tutorial = is_tutorial

        if is_tutorial:
            content = request.POST.get('content', '').strip()
            assignment.content = content
            tutorial_link = request.POST.get('tutorial_link', '').strip()
            assignment.tutorial_link = tutorial_link

            # Provide default dummy values for required fields to avoid validation error
            assignment.description = content[:100] or "Tutorial content"
            assignment.assignment_type = Assignment.ASSIGNMENT_TYPES[0][0]  # first choice as default
            assignment.due_date = None
            assignment.max_score = 0  # or 1 if 0 not allowed
            assignment.status = Assignment.STATUS_CHOICES[0][0]  # first status choice
            assignment.instructions = ""
            assignment.allow_late_submission = False
            assignment.late_penalty_per_day = 0

        else:
            description = request.POST.get('description')
            assignment_type = request.POST.get('assignment_type')
            due_date_str = request.POST.get('due_date')
            max_score = request.POST.get('max_score')
            status = request.POST.get('status')
            instructions = request.POST.get('instructions')
            downloadable_file = request.FILES.get('downloadable_content')

            allow_late_submission = bool(request.POST.get('allow_late_submission'))
            late_penalty = request.POST.get('late_penalty_per_day') or 0

            assignment.description = description
            assignment.assignment_type = assignment_type
            assignment.due_date = parse_datetime(due_date_str) if due_date_str else None
            assignment.max_score = max_score
            assignment.status = status
            assignment.instructions = instructions
            if downloadable_file:
                assignment.downloadable_file = downloadable_file
            assignment.allow_late_submission = allow_late_submission
            assignment.late_penalty_per_day = late_penalty

            assignment.content = ""

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


# ======================================== DELETE ASSIGNMENT ==================================


@login_required(login_url='login')
@staff_member_required(login_url='login')
def delete_assignment(request, id):
        
    assignment = Assignment.objects.get(id=id)
    assignment.delete()
    
    messages.success(request, "Assignment deleted successfully!")
    
    return redirect("instructor_jovac", slug=assignment.course.slug)


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


@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_mcq_question(request, course_slug, sheet_slug):
    course = get_object_or_404(Course, slug=course_slug)
    course_sheet = get_object_or_404(CourseSheet, slug=sheet_slug, course=course)

    if request.method == 'POST':
        question_text = (request.POST.get('question_text') or '').strip()
        option_a = (request.POST.get('option_a') or '').strip()
        option_b = (request.POST.get('option_b') or '').strip()
        option_c = (request.POST.get('option_c') or '').strip()
        option_d = (request.POST.get('option_d') or '').strip()
        correct_option = (request.POST.get('correct_option') or '').strip().upper()
        difficulty_level = (request.POST.get('difficulty_level') or 'Easy').strip()

        if not all([question_text, option_a, option_b, option_c, option_d, correct_option]):
            messages.error(request, 'All MCQ fields are required.')
            return render(request, 'instructor/jovac/add_mcq_question.html', {'course': course, 'sheet': course_sheet})

        mcq = MCQQuestion.objects.create(
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_option,
            explanation=(request.POST.get('explanation') or '').strip(),
            tags=(request.POST.get('tags') or '').strip(),
            difficulty_level=difficulty_level,
            is_approved=False,
        )
        course_sheet.mcq_questions.add(mcq)

        _notify_admin_approval_request(
            created_by=request.user,
            item_type='MCQ Question',
            item_name=mcq.question_text[:80],
            details_url=reverse('administrator_batches'),
        )

        messages.success(request, 'MCQ question created and sent for admin approval.')
        return redirect('instructor_jovac_sheet', course_slug=course.slug, sheet_slug=course_sheet.slug)

    return render(request, 'instructor/jovac/add_mcq_question.html', {'course': course, 'sheet': course_sheet})


@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_coding_question(request, course_slug, sheet_slug):
    course = get_object_or_404(Course, slug=course_slug)
    course_sheet = get_object_or_404(CourseSheet, slug=sheet_slug, course=course)

    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        description = (request.POST.get('description') or '').strip()
        difficulty_level = (request.POST.get('difficulty_level') or 'Easy').strip()

        if not title or not description:
            messages.error(request, 'Coding question title and description are required.')
            return render(request, 'instructor/jovac/add_coding_question.html', {'course': course, 'sheet': course_sheet})

        coding_question = Question.objects.create(
            title=title,
            description=description,
            difficulty_level=difficulty_level,
            is_approved=False,
            added_by=request.user,
        )
        course_sheet.coding_questions.add(coding_question)

        _notify_admin_approval_request(
            created_by=request.user,
            item_type='Coding Question',
            item_name=coding_question.title,
            details_url=reverse('administrator_batches'),
        )

        messages.success(request, 'Coding question created and sent for admin approval.')
        return redirect('instructor_jovac_sheet', course_slug=course.slug, sheet_slug=course_sheet.slug)

    return render(request, 'instructor/jovac/add_coding_question.html', {'course': course, 'sheet': course_sheet})

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
