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

# ========================= SHEET WORK ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def sheets(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    sheets = Sheet.objects.all().order_by('-id')
    
    parameters = {
        "instructor": instructor,
        "sheets": sheets
        
    }
    
    return render(request, 'administration/sheet/sheets.html', parameters)

# ========================= ADD SHEET ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_sheet(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    batches = Batch.objects.all()
    
    if request.method == "POST":
        
        name = request.POST.get('name')
        batches = request.POST.getlist('batches')
        thumbnail = request.FILES.get('thumbnail')
        
        sheet = Sheet.objects.create(
            name=name,
            thumbnail=thumbnail
        )
        
        for batch in batches:
            batch = Batch.objects.get(id=batch)
            sheet.batches.add(batch)
            
        sheet.save()
        
        messages.success(request, "Sheet added successfully!")
        return redirect('instructor_sheets')
    
    parameters = {
        "instructor": instructor,
        "batches": batches
    }
    
    return render(request, 'administration/sheet/add_sheet.html', parameters)

# ========================= DELETE SHEET ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def delete_sheet(request, id):
    
    sheet = get_object_or_404(Sheet, id=id)
    sheet.delete()
    
    messages.success(request, "Sheet deleted successfully!")
    return redirect('instructor_sheets')

# ========================= SHEET ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def sheet(request, slug):
    
    instructor = Instructor.objects.get(id=request.user.id)
    sheet = Sheet.objects.get(slug=slug)
    questions = sheet.questions.all()
    
    parameters = {
        "instructor": instructor,
        "sheet": sheet,
        "questions": questions
    }
    
    return render(request, 'administration/sheet/sheet.html', parameters)

# ========================= GET EXCLUDED QUESTIONS ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def get_excluded_questions(request, sheet_id):
    sheet = get_object_or_404(Sheet, id=sheet_id)
    excluded_questions = Question.objects.exclude(sheets=sheet)

    data = [
        {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "difficulty_level": question.difficulty_level,
            "difficulty_level_color": question.get_difficulty_level_color(),
        }
        for question in excluded_questions
    ]
    
    return JsonResponse(data, safe=False)

# ========================= ADD QUESTION TO SHEET ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_question_to_sheet(request, sheet_id, question_id):
    if request.method == "POST":
        sheet = get_object_or_404(Sheet, id=sheet_id)
        question = get_object_or_404(Question, id=question_id)
        
        sheet.questions.add(question)
        sheet.save()
        
        return JsonResponse({"success": True, "message": "Question added to sheet successfully."})

    return JsonResponse({"success": False, "message": "Invalid request method."})

# ========================= REMOVE QUESTION FROM SHEET ==========================

@login_required(login_url='login')
def remove_question_from_sheet(request, sheet_id, question_id):
    sheet = get_object_or_404(Sheet, id=sheet_id)
    question = get_object_or_404(Question, id=question_id)
    
    sheet.questions.remove(question)
    sheet.save()
    
    return redirect('instructor_sheet', slug=sheet.slug)

# =========================== LEADERBOARD ===========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def leaderboard(request, slug):
    
    instructor = Instructor.objects.get(id=request.user.id)
    sheet = Sheet.objects.get(slug=slug)
    
    parameters = {
        "instructor": instructor,
        "sheet": sheet,
    }
    
    return render(request, 'administration/sheet/leaderboard.html', parameters)

# ===============================================================================================
# ===============================================================================================
# ===============================================================================================
from django.db.models import Max, Sum, Min, OuterRef, Subquery

def sheet_leaderboard(request, slug):
    sheet = get_object_or_404(Sheet, slug=slug)

    # Get all questions in the sheet
    total_questions = sheet.questions.all()

    # Subquery to get the maximum score for each user and question
    max_score_subquery = Submission.objects.filter(
        user=OuterRef('user'),
        question=OuterRef('question'),
        status='Accepted'
    ).order_by('-score').values('score')[:1]

    # Annotate maximum scores and aggregate for total score and earliest submission time
    leaderboard_data = (
        Submission.objects.filter(
            question__in=total_questions,
            status='Accepted'
        )
        .values('user')  # Group by user
        .annotate(
            total_score=Sum(Subquery(max_score_subquery)),  # Sum max scores per user
            earliest_submission=Min('submitted_at')  # Get the earliest submission time
        )
        .order_by('-total_score', 'earliest_submission')  # Sort by total score and earliest submission
    )

    # Format the leaderboard data
    leaderboard = []
    for entry in leaderboard_data:
        user_id = entry['user']
        user = Student.objects.get(id=user_id)
        solved_problems = Submission.objects.filter(
            user=user_id,
            question__in=total_questions,
            status='Accepted'
        ).values('question').distinct().count()  # Count distinct problems solved by the user

        leaderboard.append({
            'student': {
                'id': user_id,
                'name': f"{user.first_name} {user.last_name}",
            },
            'total_score': entry['total_score'],
            'earliest_submission': entry['earliest_submission'],
            'solved_problems': solved_problems,
        })

    return JsonResponse({'leaderboard': leaderboard})

