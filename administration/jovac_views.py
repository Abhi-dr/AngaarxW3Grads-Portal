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

from practice.models import Streak

# ======================================== JOVAC ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def jovacs(request):
    courses = Course.objects.all()

    parameters = {
        "courses": courses,
    }

    return render(request, "administration/jovac/index.html", parameters)

# ======================================== JOVAC COURSE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def jovac(request, slug):
    course = get_object_or_404(Course, slug=slug)
    instructors = course.instructors.all()

    course_sheets = CourseSheet.objects.filter(course = course)

    # assignments = Assignment.objects.filter(
    #     content_type=course_ct,
    #     object_id=course.id
    # )

    # query = request.POST.get("query")
    # if query:
    #     assignments = Assignment.objects.filter(
    #         Q(id__icontains=query) |
    #         Q(title__icontains=query) |
    #         Q(description__icontains=query)|
    #         Q(assignment_type__icontains=query)
    #         )


    parameters = {
        "course": course,
        "instructors": instructors,
        "course_sheets": course_sheets,
        # "assignments": assignments,
    }

    return render(request, "administration/jovac/course.html", parameters)

# ======================================== JOVAC REORDER SHEETS ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def reorder_jovac_sheets(request, slug):
    """Render the drag-and-drop sheet reorder page for a JOVAC course."""
    course = get_object_or_404(Course, slug=slug)
    sheets = course.get_ordered_sheets()
    parameters = {
        "course": course,
        "sheets": sheets,
    }
    return render(request, "administration/jovac/reorder_sheets.html", parameters)



@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def jovac_sheet(request, course_slug, sheet_slug):
    course = get_object_or_404(Course, slug=course_slug)
    instructors = course.instructors.all()
    course_sheet = CourseSheet.objects.get(course = course, slug=sheet_slug)
    # Legacy server-side assignment loading is intentionally disabled here.
    # The administration sheet detail page now loads mixed sheet items via the JOVAC API.


    parameters = {
        "course": course,
        "sheet": course_sheet,
        "instructors": instructors,
    }

    return render(request, "administration/jovac/course_sheet.html", parameters)


# ======================================= EDIT COURSE SHEET ===============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def edit_sheet(request, course_slug, sheet_slug):
    course = get_object_or_404(Course, slug=course_slug)
    sheet = get_object_or_404(CourseSheet, slug=sheet_slug, course=course)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        description = request.POST.get('description')
        is_enabled = bool(request.POST.get('is_enabled'))
        is_approved = bool(request.POST.get('is_approved'))
        thumbnail = request.FILES.get('thumbnail')

        if not name:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Sheet name is required.'}, status=400)
            messages.error(request, "Sheet name is required.")
            return redirect('administrator_edit_jovac_sheet', course_slug=course.slug, sheet_slug=sheet.slug)

        sheet.name = name
        sheet.description = description
        sheet.is_enabled = is_enabled
        sheet.is_approved = is_approved

        if thumbnail:
            sheet.thumbnail = thumbnail

        sheet.save()

        if is_ajax:
            return JsonResponse({
                'success': True,
                'sheet': {
                    'name': sheet.name,
                    'description': sheet.description or '',
                    'is_enabled': sheet.is_enabled,
                    'is_approved': sheet.is_approved,
                    'thumbnail_url': sheet.thumbnail.url if sheet.thumbnail else '',
                }
            })

        messages.success(request, "Sheet updated successfully.")
        return redirect('administrator_jovac', slug=course.slug)

    context = {
        'course': course,
        'sheet': sheet,
    }
    return render(request, 'administration/jovac/edit_sheet.html', context)



# ======================================= ADD COURSE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def add_course(request):

    instructors = CustomUser.objects.filter(role='instructor')

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        my_instructors = request.POST.getlist('instructors')
        thumbnail = request.FILES.get('thumbnail')

        course = Course(
            name=name,
            description=description
        )

        course.save()

        for instructor_id in my_instructors:
            instructor = CustomUser.objects.get(id=instructor_id)
            course.instructors.add(instructor)

        course.thumbnail = thumbnail
        course.save()

        messages.success(request, "Course added successfully!")
        return redirect('administrator_jovacs')
    
    parameters = {
        "instructors": instructors,
    }
    
    return render(request, 'administration/jovac/add_course.html', parameters)

# ============================= EDIT COURSE =============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def edit_course(request, slug):
    course = Course.objects.get(slug=slug)
    instructors = CustomUser.objects.filter(role='instructor')

    if request.method == 'POST':
        course.name = request.POST.get('name')
        course.description = request.POST.get('description')
        selected_instructors = request.POST.getlist('instructors')

        if 'thumbnail' in request.FILES:
            course.thumbnail = request.FILES.get('thumbnail')

        # Clear existing instructors and add the new ones
        course.instructors.clear()
        for instructor_id in selected_instructors:
            instructor = CustomUser.objects.get(id=instructor_id)
            course.instructors.add(instructor)

        course.save()
        messages.success(request, "Course updated successfully!")
        return redirect('administrator_jovacs')

    parameters = {
        "course": course,
        "instructors": instructors,
    }

    return render(request, 'administration/jovac/edit_course.html', parameters)


# ======================================= ADD COURSE SHEET ==================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_sheet(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        thumbnail = request.FILES.get('thumbnail')
        created_by = request.user  # CustomUser IS the admin — no proxy lookup needed

        sheet = CourseSheet.objects.create(
            name=name,
            description=description,
            thumbnail=thumbnail,
            created_by=created_by,
        )
        sheet.course.add(course)

        messages.success(request, "Sheet created successfully.")
        return redirect('administrator_jovac', slug=course.slug)

    return render(request, 'administration/jovac/add_sheet.html', {'course': course})


# ================================================================================================
# ========================================= ASSIGNMENTS WORK =====================================
# ================================================================================================

# ======================================== ADD ASSIGNMENT ========================================
@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
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
        return redirect('administrator_jovac', slug=course.slug)

    context = {
        'course': course,
        'assignment_types': Assignment.ASSIGNMENT_TYPES,
        'status_choices': Assignment.STATUS_CHOICES
    }
    return render(request, 'administration/jovac/add_assignment.html', context)

# ======================================== EDIT ASSIGNMENT ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
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
            return redirect('administrator_jovac_sheet', course.slug, assignment.course_sheets.first().slug)
        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, 'administration/jovac/edit_assignment.html', {
        'assignment': assignment,
        'course': course,
        'assignment_types': Assignment.ASSIGNMENT_TYPES,
        'status_choices': Assignment.STATUS_CHOICES,
    })

# ======================================== DELETE ASSIGNMENT (STANDARD NON-AJAX VERSION) ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def delete_assignment(request, id):
        
    assignment = Assignment.objects.get(id=id)
    assignment.delete()
    
    messages.success(request, "Assignment deleted successfully!")
    
    return redirect("administrator_jovac", slug=assignment.course.slug)


# ======================================== VIEW SUBMISSIONS ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
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
    
    return render(request, "administration/jovac/submissions.html", parameters)



@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def reorder_assignments(request, slug):
    course_sheet = get_object_or_404(CourseSheet, slug=slug)
    items = course_sheet.get_ordered_items()
    administrator = request.user  # CustomUser with role='admin' — no separate table

    return render(request, 'administration/jovac/reorder.html', {
        "administrator": administrator,
        "course_sheet": course_sheet,
        "items": items
    })


@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def update_assignment_order(request, id):
    course_sheet = get_object_or_404(CourseSheet, id=id)
    order = request.POST.getlist("order[]")  # JS will send order[]=1&order[]=2

    try:
        normalized_order = []
        for item_id in order:
            item_id = (item_id or "").strip()
            if not item_id:
                continue

            # Backward-compatible: treat plain numeric IDs as assignment IDs.
            if "_" not in item_id and item_id.isdigit():
                item_id = f"assignment_{item_id}"

            normalized_order.append(item_id)

        new_order = {item_id: index for index, item_id in enumerate(normalized_order)}
        course_sheet.custom_order = new_order
        course_sheet.save()
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
