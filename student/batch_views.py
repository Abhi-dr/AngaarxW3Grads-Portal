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
    
    if not EnrollmentRequest.objects.filter(student=student, batch=batch, status='Accepted').exists():
        messages.warning(request, "Beta tu jb paida bhi nahi hua tha tbse URL s khel rha hu m🥱")
        return redirect('my_batches')
    
    sheets = Sheet.objects.filter(batches=batch)
    
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
    pod = POD.objects.filter(batch=batch).first()
    
    parameters = {
        "batch": batch,
        "sheets": sheets,
        "pod": pod,
        "progress": int(progress),
        "solved_questions": solved_questions,
        "questions_left": questions_left
    }
    
    return render(request, 'student/batch/batch.html', parameters)
    
# ========================================= MY SHEET =========================================

@login_required(login_url="login")
def my_sheet(request, slug):
    
    sheet = get_object_or_404(Sheet, slug=slug)
    
    
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