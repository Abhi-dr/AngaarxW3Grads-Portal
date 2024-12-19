from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.timezone import now
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from accounts.models import Student, Instructor
from practice.models import POD, Submission, Question, Sheet, Batch,EnrollmentRequest

from django.views.decorators.cache import cache_control
from practice.models import POD, Question, Sheet, Submission, TestCase, DriverCode

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
    
    return render(request, 'instructor/sheet/sheets.html', parameters)

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
        is_sequential = 'is_sequential' in request.POST
        
        sheet = Sheet.objects.create(
            name=name,
            thumbnail=thumbnail,
            is_sequential=is_sequential,
        )
        
        for batch in batches:
            batch = Batch.objects.get(id=batch)
            sheet.batches.add(batch)
            
        sheet.save()
        
        messages.success(request, "Sheet added successfully!")
        return redirect('instructor_sheet', slug=sheet.slug)
    
    parameters = {
        "instructor": instructor,
        "batches": batches
    }
    
    return render(request, 'instructor/sheet/add_sheet.html', parameters)


# ========================= EDIT SHEET ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def edit_sheet(request, slug):
    
    instructor = Instructor.objects.get(id=request.user.id)
    sheet = Sheet.objects.get(slug=slug)
    batches = Batch.objects.all()
    
    if request.method == "POST":
        
        name = request.POST.get('name')
        batches = request.POST.getlist('batches')
        thumbnail = request.FILES.get('thumbnail')
        is_sequential = 'is_sequential' in request.POST
        
        sheet.name = name        
        sheet.is_sequential = is_sequential
        sheet.batches.clear()
        
        if thumbnail:
            sheet.thumbnail = thumbnail
        
        for batch in batches:
            batch = Batch.objects.get(id=batch)
            sheet.batches.add(batch)
            
        sheet.save()
        
        messages.success(request, "Sheet updated successfully!")
        return redirect('instructor_sheet', slug=sheet.slug)
    
    parameters = {
        "instructor": instructor,
        "sheet": sheet,
        "batches": batches
    }
    
    return render(request, 'instructor/sheet/edit_sheet.html', parameters)

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
    questions = sheet.get_ordered_questions()
    
    parameters = {
        "instructor": instructor,
        "sheet": sheet,
        "questions": questions
    }
    
    return render(request, 'instructor/sheet/sheet.html', parameters)

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

# ========================= ADD NEW QUESTION TO SHEET ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def add_new_question(request, slug):
    sheet = get_object_or_404(Sheet, slug=slug)
    instructor = Instructor.objects.get(id=request.user.id)
    
    if request.method == "POST":
        title = request.POST.get('title')
        scenario = request.POST.get('scenario')
        description = request.POST.get('description')
        constraints = request.POST.get('constraints')
        difficulty_level = request.POST.get('difficulty_level')
        
        question = Question(
            title=title,
            scenario=scenario,
            description=description,
            constraints = constraints,
            difficulty_level=difficulty_level,
            is_approved=True
        )
        
        question.save()
        
        sheet.questions.add(question)
        
        messages.success(request, "Question added successfully!")
        return redirect('instructor_sheet', slug=sheet.slug)
    
    parameters = {
        "instructor": instructor,
        "sheet": sheet,
    }
    
    return render(request, 'instructor/sheet/add_new_question.html', parameters)
        
        
    
    

# ========================= MAKE DUPLICATE ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def make_duplicate(request, sheet_id, question_id):
    
    sheet = Sheet.objects.get(id = sheet_id)
    
    if request.method == "POST":
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

# ========================= REORDER SHEET QUESTIONS ==========================

def reorder(request, slug):
    sheet = get_object_or_404(Sheet, slug=slug)
    questions = sheet.get_ordered_questions()
    instructor = Instructor.objects.get(id=request.user.id)
    
    parameters = {
        "instructor": instructor,
        "sheet": sheet,
        "questions": questions
    }
    
    return render(request, 'instructor/sheet/reorder.html', parameters)

# ========================= UPDATE SHEET ORDER ==========================

def update_sheet_order(request, sheet_id):
    if request.method == 'POST':
        sheet = get_object_or_404(Sheet, id=sheet_id)
        order = request.POST.getlist('order')[0].split(",") #  ['39,40,41,46,95,72,53']
        order = [int(qid) for qid in order]
        
        print("\n\n", order)
        try:
            # Update the custom_order field with the new positions
            sheet.custom_order = {qid: idx for idx, qid in enumerate(order)}
            sheet.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


# ============================= SET SHEET TIMER =============================

@csrf_exempt
def set_sheet_timer(request, sheet_id):
    if request.method == 'POST':
        sheet = get_object_or_404(Sheet, id=sheet_id)

        # Parse the incoming data
        data = json.loads(request.body)
        start_time  = data.get("start_time")
        end_time = data.get('end_time')

        if start_time and end_time:
            sheet.start_time = start_time 
            sheet.end_time = end_time
        else:
            # If end_time is None, reset the timer
            sheet.start_time = None
            sheet.end_time = None

        sheet.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)

# ============================= FETCH SHEET TIMER =============================

def fetch_sheet_timer(request, sheet_id):
    sheet = get_object_or_404(Sheet, id=sheet_id)
    if sheet.end_time:
        remaining_time = sheet.end_time - now()
        return JsonResponse({
            'sheet_name': sheet.name,
            'start_time': sheet.start_time.isoformat(),
            'end_time': sheet.end_time.isoformat(),
            'remaining_time': remaining_time.total_seconds() if remaining_time.total_seconds() > 0 else 0,
        })
    return JsonResponse({'sheet_name': sheet.name, 'end_time': None, 'remaining_time': 0})

# ===============================================================================================
# ===============================================================================================
# ===============================================================================================
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
    
    return render(request, 'instructor/sheet/leaderboard.html', parameters)


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

# =========================================== DOWNLOAD LEADERBOARD =============================
import pandas as pd
from django.http import HttpResponse
from django.utils.timezone import make_naive

def download_leaderboard_excel(request, slug):
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

    # Format leaderboard data for DataFrame
    leaderboard = []
    for user_id, data in user_scores.items():
        user = Student.objects.get(id=user_id)
        total_score = sum(data[qid] for qid in data if isinstance(qid, int))  # Sum scores for questions
        solved_problems = len(data['solved_questions'])

        # Convert timezone-aware datetime to naive
        earliest_submission_naive = make_naive(data['earliest_submission'])

        leaderboard.append({
            'Student ID': user_id,
            'Student Name': f"{user.first_name} {user.last_name}",
            'Total Score': total_score,
            'Earliest Submission': earliest_submission_naive,
            'Solved Problems': solved_problems,
        })

    # Create a DataFrame from the leaderboard data
    df = pd.DataFrame(leaderboard)

    # Generate Excel file
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="leaderboard_{slug}.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Leaderboard")

    return response


# ======================================== TEST CASES ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def test_cases(request, slug):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
    question = Question.objects.get(slug=slug)
    
    test_cases = TestCase.objects.filter(question=question)
    
    parameters = {
        'instructor': instructor,
        'question': question,
        'test_cases': test_cases
    }
    return render(request, 'instructor/sheet/test_cases.html', parameters)



# ======================================== ADD TEST CASE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def add_test_case(request, slug):
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        question = Question.objects.get(slug=slug)
        
        input_data = request.POST.get('input_data')
        expected_output = request.POST.get('expected_output')
        is_sample = 'is_sample' in request.POST
        
        test_case = TestCase(
            question=question,
            input_data=input_data,
            expected_output=expected_output,
            is_sample=is_sample
        )
        test_case.save()
        
        # Return the newly added test case as JSON
        return JsonResponse({
            'status': 'success',
            'message': 'Test case added successfully.',
            'test_case': {
                'id': test_case.id,
                'input_data': test_case.input_data,
                'expected_output': test_case.expected_output,
                'is_sample': test_case.is_sample
            }
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)


# ======================================== EDIT TEST CASE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def edit_test_case(request, id):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
    test_case = TestCase.objects.get(id=id)
    
    if request.method == 'POST':
        
        input_data = request.POST.get('input_data')
        expected_output = request.POST.get('expected_output')
        is_sample = 'is_sample' in request.POST
                
        test_case.input_data = input_data
        test_case.expected_output = expected_output
        test_case.is_sample = is_sample

        test_case.save()
        
        
        messages.success(request, 'Test case updated successfully')
        return redirect('instructor_test_cases', slug=test_case.question.slug)
    
    parameters = {
        'instructor': instructor,
        'test_case': test_case
    }
    
    return render(request, 'instructor/sheet/edit_test_case.html', parameters)

# ======================================== DELETE TEST CASE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def delete_test_case(request, id):
    
    test_case = TestCase.objects.get(id=id)
    
    test_case.delete()
    
    messages.success(request, 'Test case deleted successfully')
    return redirect('test_cases', slug=test_case.question.slug)


# ======================================== DRIVER CODE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def driver_code(request, slug):
    
    instructor = Instructor.objects.get(id=request.user.id)
    question = Question.objects.get(slug=slug)
    
    driver_codes = {code.language_id: code.code for code in DriverCode.objects.filter(question=question)}
    
        
    if request.method == 'POST':
        
        language_id = request.POST.get('language_id')
        code = request.POST.get('code')

        # Check if a driver code already exists for the given language
        existing_code = DriverCode.objects.filter(question=question, language_id=language_id).first()
        if existing_code:
            existing_code.code = code
            existing_code.save()
            return JsonResponse({"success": True, "message": f"Driver code for {question.title} updated successfully."})
        else:
            driver_code = DriverCode(question=question, language_id=language_id, code=code)
            driver_code.save()
            return JsonResponse({"success": True, "message": f"Driver code for {question.title} added successfully."})

    parameters = {
        "instructor": instructor,
        'question': question,
        'driver_codes': driver_codes
    }

    return render(request, 'instructor/sheet/driver_code.html', parameters)


# ======================================== TEST CODE ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def test_code(request, slug):
    
    instructor = Instructor.objects.get(id=request.user.id)
    question = get_object_or_404(Question, slug=slug)
    sample_test_cases = TestCase.objects.filter(question=question, is_sample=True)
    
    parameters = {
        'instructor': instructor,
        'question': question,
        'sample_test_cases': sample_test_cases
    }
    
    return render(request, 'instructor/sheet/test_code.html', parameters)
