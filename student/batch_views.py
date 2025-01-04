from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.utils import timezone
from datetime import datetime
from django.db.models import Q
from django.http import JsonResponse

from accounts.models import Student, Instructor
from student.models import Notification, Anonymous_Message, Feedback
from practice.models import POD, Submission, Question, Sheet, Batch,EnrollmentRequest

# ========================================= DASHBOARD =========================================

@login_required(login_url="login")
def my_batches(request):
    
    student = request.user.student
    
    student_batches = Batch.objects.filter(
        enrollment_requests__student=student,
        enrollment_requests__status='Accepted'
    )

    all_batches = Batch.objects.exclude(
        enrollment_requests__student=student,
        enrollment_requests__status='Accepted'
    )
    
    parameters = {
        "all_batches": all_batches,
        "student_batches": student_batches
    }
    
    return render(request, 'student/batch/my_batches.html', parameters)

# ========================================= ENROLL BATCH ========================================

@login_required(login_url="login")
def enroll_batch(request, id):
    student = request.user.student
    batch = get_object_or_404(Batch, id=id)
    
    # Check if the student is already enrolled or has a pending request
    if not EnrollmentRequest.objects.filter(student=student, batch=batch).exists():
        EnrollmentRequest.objects.create(student=student, batch=batch)
        messages.success(request, "Your enrollment request has been submitted!")
    else:
        messages.warning(request, "You have already requested to join this batch.")
    
    return redirect('my_batches')
    
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
    
    # PROGRESS OF ALL THE QUESTION SOLVED BY THE STUDENT
    total_questions = 0
    solved_questions = 0
    for sheet in sheets:
        total_questions += sheet.questions.count()
        solved_questions += sheet.get_solved_questions(student)
    
    if total_questions == 0:
        progress = 0
    else:
        progress = (solved_questions / total_questions) * 100
    
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
        "notifications": notifications
    }
    
    return render(request, 'student/batch/batch.html', parameters)
    
# ========================================= MY SHEET =========================================

@login_required(login_url="login")
def my_sheet(request, slug):
    
    sheet = get_object_or_404(Sheet, slug=slug)
    
    if not sheet.is_enabled:
        messages.info(request, "This sheet is not enabled.")
        return redirect('batch' , slug=sheet.batches.first().slug)
    
    parameters = {
        "sheet": sheet
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
from django.db.models import Count, Min, Max

def student_fetch_batch_leaderboard(request, slug):    
    
    start = timezone.now()
    
    batch = get_object_or_404(Batch, slug=slug)
    sheets = batch.sheets.all()
    total_questions = Question.objects.filter(sheets__in=sheets).distinct()

    # Aggregate submission data at the database level
    submissions = Submission.objects.filter(
        question__in=total_questions,
        status='Accepted'
    ).values(
        'user_id', 'question_id', 'question__sheets__id'
    ).annotate(
        max_score=Max('score'),
        earliest_submission=Min('submitted_at')
    )

    # Process aggregated data
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

        # Add score
        user_scores[user_id]['total_score'] += sub['max_score']
        user_scores[user_id]['earliest_submission'] = min(
            user_scores[user_id]['earliest_submission'], sub['earliest_submission']
        )
        user_scores[user_id]['solved_questions'].add(question_id)

        # Sheet breakdown
        if sheet_id not in user_scores[user_id]['sheet_breakdown']:
            user_scores[user_id]['sheet_breakdown'][sheet_id] = 0
        user_scores[user_id]['sheet_breakdown'][sheet_id] += 1

    # Format leaderboard
    leaderboard = []
    solved_question_counts = {}

    for user_id, data in user_scores.items():
        user = Student.objects.get(id=user_id)
        solved_problems = len(data['solved_questions'])

        # Map sheet IDs to sheet names
        sheet_details = {
            Sheet.objects.get(id=sheet_id).name: count
            for sheet_id, count in data['sheet_breakdown'].items()
        }

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

        if solved_problems not in solved_question_counts:
            solved_question_counts[solved_problems] = 0
        solved_question_counts[solved_problems] += 1

    # Sort leaderboard by total score and earliest submission
    leaderboard.sort(key=lambda x: (-x['total_score'], x['earliest_submission']))
    
    end = timezone.now()
    
    print(f"Time taken: {end - start}")

    return JsonResponse({
        'leaderboard': leaderboard,
        'solved_question_counts': solved_question_counts
    })
