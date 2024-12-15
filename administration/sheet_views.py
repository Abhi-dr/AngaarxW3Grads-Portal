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

# ========================= TOGGLE SHEET STATUS ==========================

@login_required
@staff_member_required
def toggle_sheet_status(request, slug):
    if request.method == "POST":
        sheet = get_object_or_404(Sheet, slug=slug)
        sheet.is_enabled = not sheet.is_enabled
        sheet.save()
        return JsonResponse({'status': sheet.is_enabled})

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

# ========================= ADD NEW QUESTION ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def make_duplicate(request, slug):
    
    sheet = Sheet.objects.get(slug = slug)
    
    if request.method == "POST":
        question_id = request.POST.get('question_id')
        # make a copy of the question of the question id's question
        question = Question.objects.get(id=question_id)
        new_question = Question.objects.create(
            title=question.title + "- (Copy)",
            scenario=question.scenario,
            description=question.description,
            constraints=question.constraints,
            
            input_format=question.input_format,
            output_format=question.output_format,
            
            cpu_time_limit=question.cpu_time_limit,
            memory_limit=question.memory_limit,
            
            difficulty_level=question.difficulty_level,
            
            youtube_link=question.youtube_link,
            hint=question.hint,
            
            is_approved=True,
            parent_id=question.id
        )
        
        new_question.save()
        sheet.questions.add(new_question)
        sheet.save()
        
        # TEST CASE AND DRIVER CODE COPY
        for test_case in question.test_cases.all():
            new_test_case = test_case
            new_test_case.id = None
            new_test_case.question = new_question
            new_test_case.save()
            
        for driver_code in question.driver_codes.all():
            new_driver_code = driver_code
            new_driver_code.id = None
            new_driver_code.question = new_question
            new_driver_code.save()
        
        
        messages.success(request, "Question added successfully!")
        return redirect('instructor_sheet', slug=sheet.slug)

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
from django.db.models import Max, Sum, Min, OuterRef, Subquery, Count

def sheet_leaderboard(request, slug):
    sheet = get_object_or_404(Sheet, slug=slug)
    total_questions = sheet.questions.all()

    # Fetch all submissions for the sheet
    submissions = Submission.objects.filter(
        question__in=total_questions,
        status='Accepted'
    )

    # Dictionary to store max scores for each user
    user_scores = {}
    for submission in submissions:
        user_id = submission.user.id
        question_id = submission.question.id

        # Initialize user entry if not present
        if user_id not in user_scores:
            user_scores[user_id] = {
                'total_score': 0,
                'earliest_submission': submission.submitted_at,
                'solved_questions': set(),
            }

        # Update max score for the question
        current_max_score = user_scores[user_id].get(question_id, 0)
        user_scores[user_id][question_id] = max(current_max_score, submission.score)

        # Update earliest submission
        user_scores[user_id]['earliest_submission'] = min(
            user_scores[user_id]['earliest_submission'], submission.submitted_at
        )

        # Track solved questions
        user_scores[user_id]['solved_questions'].add(question_id)

    # Format leaderboard data
    leaderboard = []
    for user_id, data in user_scores.items():
        user = Student.objects.get(id=user_id)
        total_score = sum(data[qid] for qid in data if isinstance(qid, int))  # Sum scores for questions
        solved_problems = len(data['solved_questions'])

        leaderboard.append({
            'student': {
                'id': user_id,
                'name': f"{user.first_name} {user.last_name}",
            },
            'total_score': total_score,
            'earliest_submission': data['earliest_submission'],
            'solved_problems': solved_problems,
        })

    leaderboard.sort(key=lambda x: (-x['total_score'], x['earliest_submission']))
    
    # i need the count of students solving how many questions


    return JsonResponse({'leaderboard': leaderboard})

