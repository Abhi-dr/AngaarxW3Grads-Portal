from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.utils import timezone
from datetime import datetime
from django.db.models import Q, Case, When, Value, CharField
from django.http import JsonResponse

from django.core.paginator import Paginator, EmptyPage

from django.db.models import Count, Min, Max

from accounts.models import Student
from student.models import Notification, Course
from practice.models import Submission, Question, Sheet, Batch,EnrollmentRequest, MCQQuestion, MCQSubmission

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# ========================================= DASHBOARD =========================================

@login_required(login_url="login")
def my_batches(request):
    return render(request, 'student/batch/my_batches.html')


@login_required(login_url="login")
def fetch_my_batch_data(request):
    """API endpoint to fetch batch and course data as JSON"""
    try:
        student = request.user.student
        
        # Fetch all batches with their enrollment status for the current student
        all_batches = Batch.objects.annotate(
                enrollment_status=Case(
                    When(enrollment_requests__student=student, enrollment_requests__status='Accepted', then=Value('Accepted')),
                    When(enrollment_requests__student=student, enrollment_requests__status='Pending', then=Value('Pending')),
                    When(enrollment_requests__student=student, enrollment_requests__status='Rejected', then=Value('Rejected')),
                    default=Value('Not Enrolled'),
                    output_field=CharField(),
                )
            ).select_related().distinct()  # Ensure distinct batches

        student_batches = all_batches.filter(enrollment_status='Accepted')
        pending_batches = all_batches.filter(enrollment_status='Pending')
        rejected_batches = all_batches.filter(enrollment_status='Rejected')
        other_batches = [batch for batch in all_batches if batch not in student_batches and batch not in pending_batches and batch not in rejected_batches]
        
        # ======== COURSE REGISTRATIONS ========
        all_courses = Course.objects.annotate(
            registration_status=Case(
                When(courseregistration__student=student, courseregistration__status='Approved', then=Value('Approved')),
                When(courseregistration__student=student, courseregistration__status='Pending', then=Value('Pending')),
                When(courseregistration__student=student, courseregistration__status='Rejected', then=Value('Rejected')),
                default=Value('Not Enrolled'),
                output_field=CharField(),
            )
        ).prefetch_related('courseregistration_set').distinct()

        approved_courses = all_courses.filter(registration_status='Approved')
        pending_courses = all_courses.filter(registration_status='Pending')
        rejected_courses = all_courses.filter(registration_status='Rejected')
        other_courses = [course for course in all_courses if course not in approved_courses and course not in pending_courses and course not in rejected_courses]

        # Serialize batch data
        def serialize_batch(batch):
            return {
                'id': batch.id,
                'name': batch.name,
                'slug': batch.slug,
                'thumbnail': batch.thumbnail.url if batch.thumbnail else '',
                'required_fields': batch.required_fields if hasattr(batch, 'required_fields') else [],
            }
        
        # Serialize course data
        def serialize_course(course):
            return {
                'id': course.id,
                'name': course.name,
                'slug': course.slug,
                'thumbnail': course.thumbnail.url if course.thumbnail else '',
                'instructor_names': course.get_instructor_names(),  # Fixed: Call the method
            }

        # Build response data
        data = {
            'success': True,
            'batches': {
                'student_batches': [serialize_batch(b) for b in student_batches],
                'pending_batches': [serialize_batch(b) for b in pending_batches],
                'rejected_batches': [serialize_batch(b) for b in rejected_batches],
                'other_batches': [serialize_batch(b) for b in other_batches],
            },
            'courses': {
                'approved_courses': [serialize_course(c) for c in approved_courses],
                'pending_courses': [serialize_course(c) for c in pending_courses],
                'rejected_courses': [serialize_course(c) for c in rejected_courses],
                'other_courses': [serialize_course(c) for c in other_courses],
            }
        }
        
        return JsonResponse(data)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ========================================= ENROLL BATCH ========================================

@login_required(login_url="login")
def enroll_batch(request, id):
    student = request.user.student
    batch = get_object_or_404(Batch, id=id)

    if EnrollmentRequest.objects.filter(student=student, batch=batch).exists():
        messages.warning(request, "You have already requested to join this batch.")
        return redirect('my_batches')

    extra_data = {}
    if batch.required_fields:
        for field in batch.required_fields:
            # Special handling for college_name field
            if field.lower() == 'college_name':
                # Check if user selected "Other" and entered custom college name
                custom_college = request.POST.get(f"{field}_custom", "").strip()
                if custom_college:
                    extra_data[field] = custom_college
                else:
                    extra_data[field] = request.POST.get(field, "")
            else:
                extra_data[field] = request.POST.get(field, "")

    EnrollmentRequest.objects.create(student=student, batch=batch, additional_data=extra_data,  status="Accepted")

    messages.success(request, "You have successfully enrolled in the batch!")
    return redirect('batch', slug=batch.slug)

    
# ========================================= BATCH =========================================

@login_required(login_url="login")
def batch(request, slug):
    batch = get_object_or_404(Batch, slug=slug)
    student = request.user.student
    notifications = Notification.objects.filter(expiration_date__gt=timezone.now(), is_alert=True)

    
    if not EnrollmentRequest.objects.filter(student=student, batch=batch, status='Accepted').exists():
        messages.warning(request, "Beta tu jb paida bhi nahi hua tha tbse URL s khel rha hu m🥱")
        return redirect('my_batches')
    
    sheets = Sheet.objects.filter(batches=batch, is_approved=True).order_by('-id')
    
    # PROGRESS OF ALL THE QUESTION SOLVED BY THE STUDENT (Updated Logic)
    total_questions = 0
    solved_questions = 0
    
    # Count questions from non-sequential sheets only (accessible to all students)
    for sheet in sheets:
        total_questions += sheet.questions.filter(is_approved=True).count()
        solved_questions += sheet.get_solved_questions(student)
    
    
    if total_questions == 0:
        progress = 0
        total_questions_solved_percentage = 0
    else:
        progress = (solved_questions / total_questions) * 100
        total_questions_solved_percentage = int(progress)
    
    questions_left = total_questions - solved_questions
        
    # today's batch pod
    pod = batch.get_today_pod_for_batch()
    
    parameters = {
        "batch": batch,
        "sheets": sheets,
        "pod": pod,
        "progress": int(progress),
        "solved_questions": solved_questions,
        "questions_left": questions_left,
        "total_questions_solved_percentage": total_questions_solved_percentage,
        "notifications": notifications
    }
    
    return render(request, 'student/batch/batch.html', parameters)
    
# ========================================= MY SHEET =========================================

@login_required(login_url="login")
def my_sheet(request, slug):
    
    sheet = get_object_or_404(Sheet, slug=slug, is_approved=True)
    
    enabled_questions = sheet.get_enabled_questions_for_user(request.user.student)

    if sheet.sheet_type == "MCQ":

        user_submissions = {
            submission.question.id: submission for submission in MCQSubmission.objects.filter(student=request.user, question__in=enabled_questions)
        }

    else:

        user_submissions = {
            submission.question.id: submission for submission in Submission.objects.filter(user=request.user, question__in=enabled_questions)
            }

    
    if not sheet.is_enabled:
        messages.info(request, "This sheet is not enabled.")
        return redirect('practice')

    parameters = {
        "sheet": sheet,
        "enabled_questions": enabled_questions,
        "user_submissions": user_submissions,  # Pass the submissions to the template
    }   
    
    return render(request, 'student/batch/my_sheet.html', parameters)

# ========================================= SHEET PROGRESS ===================================

@login_required(login_url="login")
def sheet_progress(request, sheet_id):
    sheet = get_object_or_404(Sheet, id=sheet_id)
    student = request.user.student
    progress = sheet.get_progress(student)

    return JsonResponse({"progress": progress})

# ========================================= FETCH QUESTIONS =========================================

@login_required(login_url="login")
def fetch_sheet_questions(request, id):
    
    query = request.GET.get("query", "").strip()
    sheet = get_object_or_404(Sheet, id=id)
    
    questions = sheet.questions.filter(is_approved=True)
    
    if query:
        questions = questions.filter(
            Q(title__icontains=query) | 
            Q(slug__icontains=query) | 
            Q(id__icontains=query)
        )
    
    data = [
        {
            "id": question.id,
            "title": question.title,
            "difficulty_level": question.difficulty_level,
            "difficulty_color": question.get_difficulty_level_color(),
            "youtube_link": question.youtube_link,
            "slug": question.slug,
            "status": question.get_user_status(request.user.student),
            "color": question.get_status_color(request.user.student)
        }
        for question in questions
    ]
    return JsonResponse({"questions": data})

# ========================================== BATCH LEADERBOARD ======================================

@login_required(login_url="login")
def student_batch_leaderboard(request, slug):
    batch = Batch.objects.get(slug=slug)
    
    parameters = {
        "batch": batch
    }
    
    return render(request, "student/batch/leaderboard.html", parameters)

# ==================================== FETCH LEADERBOARD ======================

def student_fetch_batch_leaderboard(request, slug):
    start = timezone.now()

    batch = get_object_or_404(Batch, slug=slug)

    sheet_ids = list(batch.sheets.values_list('id', flat=True))

    submissions = Submission.objects.filter(
        question__sheets__id__in=sheet_ids,
        status='Accepted'
    ).values(
        'user_id', 'question_id', 'question__sheets__id'
    ).annotate(
        max_score=Max('score'),
        earliest_submission=Min('submitted_at')
    )

    user_ids_to_fetch = {sub['user_id'] for sub in submissions}
    sheet_ids_to_fetch = {sub['question__sheets__id'] for sub in submissions}

    student_map = Student.objects.in_bulk(user_ids_to_fetch)
    sheet_map = Sheet.objects.in_bulk(sheet_ids_to_fetch)

    user_scores = {}

    for sub in submissions:
        user_id = sub['user_id']
        question_id = sub['question_id']
        sheet_id = sub['question__sheets__id']

        if user_id not in user_scores:
            user_scores[user_id] = {
                'total_score': 0,
                'earliest_submission': sub['earliest_submission'],
                'solved_questions': set(),
                'sheet_breakdown': {}
            }

        user_scores[user_id]['total_score'] += sub['max_score']

        if sub['earliest_submission'] < user_scores[user_id]['earliest_submission']:
            user_scores[user_id]['earliest_submission'] = sub['earliest_submission']

        user_scores[user_id]['solved_questions'].add(question_id)

        user_scores[user_id]['sheet_breakdown'][sheet_id] = (
            user_scores[user_id]['sheet_breakdown'].get(sheet_id, 0) + 1
        )

    leaderboard = []
    solved_question_counts = {}

    for user_id, data in user_scores.items():
        user = student_map.get(user_id)
        if not user:
            continue

        solved_problems = len(data['solved_questions'])

        sheet_details = {}
        for s_id, count in data['sheet_breakdown'].items():
            sheet_obj = sheet_map.get(s_id)
            if sheet_obj:
                sheet_details[sheet_obj.name] = count

        leaderboard.append({
            'student': {
                'id': user_id,
                'name': f"{user.first_name} {user.last_name}",
            },
            'total_score': data['total_score'],
            'earliest_submission': data['earliest_submission'],
            'solved_problems': solved_problems,
            'sheet_breakdown': sheet_details,
        })

        solved_question_counts[solved_problems] = (
            solved_question_counts.get(solved_problems, 0) + 1
        )

    # =============================
    # SORT BEFORE PAGINATION
    # =============================
    leaderboard.sort(
        key=lambda x: (-x['total_score'], x['earliest_submission'])
    )

    # =============================
    # ADD RANK TO ALL ENTRIES
    # =============================
    for idx, entry in enumerate(leaderboard, start=1):
        entry['rank'] = idx

    # =============================
    # PAGINATION (PAGE SIZE = 10)
    # =============================
    page_number = request.GET.get('page', 1)
    paginator = Paginator(leaderboard, 10)

    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    end = timezone.now()
    print(f"Time taken: {end - start}")

    return JsonResponse({
        'leaderboard': list(page_obj),
        'pagination': {
            'current_page': page_obj.number,
            'page_size': 10,
            'total_pages': paginator.num_pages,
            'total_students': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        },
        'solved_question_counts': solved_question_counts
    })