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
from angaar_hai.custom_decorators import admin_required
from django.db import transaction
from django.urls import reverse

from accounts.models import Student, Administrator
from practice.models import POD, Submission, Question, Sheet, Batch,EnrollmentRequest, RecommendedQuestions, TestCase, DriverCode, MCQQuestion, MCQSubmission, QuestionImage

# ========================= SHEET WORK ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def sheets(request):
    # Data is sent by staff_fetch_all_sheets
    return render(request, 'administration/sheet/sheets.html')

# ========================= ADD SHEET ==========================


@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def add_sheet(request):
    administrator = get_object_or_404(Administrator, id=request.user.id)
    batches = Batch.objects.all()
    
    if request.method == "POST":
        name = request.POST.get('name')
        batch_ids = request.POST.getlist('batches')
        thumbnail = request.FILES.get('thumbnail')
        is_sequential = 'is_sequential' in request.POST
        
        # Get the new sheet_type value from the form
        sheet_type = request.POST.get('sheet_type')
        
        # Create the sheet object with all necessary fields
        sheet = Sheet.objects.create(
            name=name,
            thumbnail=thumbnail,
            is_sequential=is_sequential,
            sheet_type=sheet_type  # Add the sheet type here
        )
        
        # More efficient way to add many-to-many relationships
        if batch_ids:
            sheet.batches.set(batch_ids)
            
        messages.success(request, "Sheet added successfully!")
        return redirect('administrator_sheet', slug=sheet.slug)
    
    parameters = {
        "administrator": administrator,
        "batches": batches
    }
    
    return render(request, 'administration/sheet/add_sheet.html', parameters)

# ========================= EDIT SHEET ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def edit_sheet(request, slug):
    administrator = get_object_or_404(Administrator, id=request.user.id)
    sheet = get_object_or_404(Sheet, slug=slug)
    batches = Batch.objects.all()
    
    if request.method == "POST":
        name = request.POST.get('name')
        batch_ids = request.POST.getlist('batches')
        thumbnail = request.FILES.get('thumbnail')
        is_sequential = 'is_sequential' in request.POST
        
        # Get the sheet_type value from the form
        sheet_type = request.POST.get('sheet_type')
        
        # Update the sheet object
        sheet.name = name        
        sheet.is_sequential = is_sequential
        sheet.sheet_type = sheet_type # Update the sheet type here
        
        if thumbnail:
            sheet.thumbnail = thumbnail
            
        # More efficient way to update many-to-many relationships
        sheet.batches.set(batch_ids)
            
        sheet.save()
        
        messages.success(request, "Sheet updated successfully!")
        return redirect('administrator_sheet', slug=sheet.slug)
    
    parameters = {
        "administrator": administrator,
        "sheet": sheet,
        "selected_batch_ids": list(sheet.batches.values_list('id', flat=True)),
        "batches": batches
    }
    
    return render(request, 'administration/sheet/edit_sheet.html', parameters)

# ========================= DELETE SHEET ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def delete_sheet(request, id):
    
    sheet = get_object_or_404(Sheet, id=id)
    sheet.delete()
    
    messages.success(request, "Sheet deleted successfully!")
    return redirect('administrator_sheets')


# ========================= PENDING SHEET ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def administrator_pending_sheet(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    sheets = Sheet.objects.filter(is_approved=False).order_by("-id")
    
    parameters = {
        "administrator": administrator,
        "sheets": sheets
    }
    
    return render(request, 'administration/sheet/pending_sheets.html', parameters)

# ========================= APPROVE SHEET ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def administrator_approve_sheet(request, id):
    
    sheet = get_object_or_404(Sheet, id=id)
    sheet.is_approved = True
    sheet.save()
    
    messages.success(request, "Sheet approved successfully!")
    return redirect('administrator_pending_sheet')

# ========================= SHEET ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def sheet(request, slug):
    
    administrator = Administrator.objects.get(id=request.user.id)
    sheet = Sheet.objects.get(slug=slug)

    questions = sheet.get_ordered_questions()    
    
    parameters = {
        "administrator": administrator,
        "sheet": sheet,
        "questions": questions
    }
    
    return render(request, 'administration/sheet/sheet.html', parameters)


# ========================= TOGGLE SHEET STATUS ==========================

@login_required
@staff_member_required
@admin_required
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
@admin_required
def add_new_question(request, slug):
    sheet = get_object_or_404(Sheet, slug=slug)
    administrator = Administrator.objects.get(id=request.user.id)

    if request.method == "POST":
        title = request.POST.get('title')
        scenario = request.POST.get('scenario')
        description = request.POST.get('description')
        input_format = request.POST.get('input_format')
        output_format = request.POST.get('output_format')
        constraints = request.POST.get('constraints')
        hint = request.POST.get('hint')
        difficulty_level = request.POST.get('difficulty_level')

        # Save new question
        question = Question.objects.create(
            title=title,
            scenario=scenario,
            description=description,
            input_format=input_format,
            output_format=output_format,
            constraints=constraints,
            hint=hint,
            difficulty_level=difficulty_level,
            is_approved=True
        )

        # ==> ADD THIS BLOCK TO HANDLE IMAGE UPLOADS <==
        images = request.FILES.getlist('images')
        captions = request.POST.getlist('captions')

        # Use zip to pair each image with its corresponding caption
        for image, caption in zip(images, captions):
            # We only create an image record if a file was actually uploaded
            if image:
                QuestionImage.objects.create(
                    image=image,
                    caption=caption,
                    content_object=question  # This links the image to the new coding question
                )

        # Link question to sheet
        sheet.questions.add(question)

        # Handle Recommended Questions
        try:
            recommended_questions_data = json.loads(request.POST.get("recommended_questions", "[]"))

            for rq in recommended_questions_data:
                if rq["title"] and rq["platform"] and rq["link"]:
                    RecommendedQuestions.objects.create(
                        question=question,
                        title=rq["title"],
                        platform=rq["platform"],
                        link=rq["link"]
                    )

        except json.JSONDecodeError:
            # It's better to handle the error gracefully
            messages.error(request, "There was an error processing recommended questions.")
            # Continue without returning, or handle as you see fit

        messages.success(request, "Question and images added successfully!")
        return redirect('administrator_sheet', slug=sheet.slug)

    parameters = {
        "administrator": administrator,
        "sheet": sheet,
    }

    return render(request, 'administration/sheet/add_new_question.html', parameters)


# ========================= ADD NEW QUESTION TO SHEET USING JSON ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
@csrf_exempt
def add_question_json(request, slug):
    sheet = get_object_or_404(Sheet, slug=slug)
    
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        print("trying...")
        try:
            json_data = request.POST.get("json_data")
            data = json.loads(json_data)
            
            # Validate required fields
            required_fields = ['title', 'description', 'input_format', 'output_format', 'constraints', 'difficulty_level']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Required field "{field}" is missing or empty.'
                    })
            
            # Validate difficulty_level
            valid_difficulty_levels = ['Easy', 'Medium', 'Hard']
            if data['difficulty_level'] not in valid_difficulty_levels:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid difficulty level. Must be one of: {", ".join(valid_difficulty_levels)}'
                })
                
            # Create the question
            with transaction.atomic():
                question = Question(
                    title=data['title'],
                    scenario=data.get('scenario', ''),
                    description=data['description'],
                    input_format=data['input_format'],
                    output_format=data['output_format'],
                    constraints=data['constraints'],
                    hint=data.get('hint', ''),
                    difficulty_level=data['difficulty_level'],
                    is_approved=True
                )
                question.save()
                
                # Add question to sheet
                sheet.questions.add(question)
                
                # Handle Recommended Questions if included
                if 'recommended_questions' in data and isinstance(data['recommended_questions'], list):
                    recommended_questions = []
                    for rq in data['recommended_questions']:
                        if all(key in rq for key in ['title', 'platform', 'link']):
                            recommended_questions.append(RecommendedQuestions(
                                question=question,
                                title=rq['title'],
                                platform=rq['platform'],
                                link=rq['link']
                            ))
                    
                    if recommended_questions:
                        RecommendedQuestions.objects.bulk_create(recommended_questions)
                
                # Process test cases if included
                if 'test_cases' in data and isinstance(data['test_cases'], list):
                    test_cases = []
                    for tc in data['test_cases']:
                        if 'input' in tc and 'output' in tc:
                            test_cases.append(TestCase(
                                question=question,
                                input_data=tc['input'],
                                expected_output=tc['output'],
                                is_sample=tc.get('is_sample', False)
                            ))
                    
                    if test_cases:
                        TestCase.objects.bulk_create(test_cases)
                
                # Process driver codes if included
                if 'driver_codes' in data and isinstance(data['driver_codes'], list):
                    driver_codes = []
                    for dc in data['driver_codes']:
                        if all(key in dc for key in ['language_id', 'visible_driver_code', 'complete_driver_code']):
                            driver_codes.append(DriverCode(
                                question=question,
                                language_id=dc['language_id'],
                                visible_driver_code=dc['visible_driver_code'],
                                complete_driver_code=dc['complete_driver_code']
                            ))
                    
                    if driver_codes:
                        DriverCode.objects.bulk_create(driver_codes)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Question added successfully!',
                'redirect_url': reverse('administrator_sheet', args=[sheet.slug])
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON format. Please check your JSON data.'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'An error occurred: {str(e)}'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

# ========================= MAKE DUPLICATE ==========================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
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
        return redirect('administrator_sheet', slug=sheet.slug)

# ========================= REMOVE QUESTION FROM SHEET ==========================

@login_required(login_url='login')
@admin_required
def remove_question_from_sheet(request, sheet_id, question_id):
    sheet = get_object_or_404(Sheet, id=sheet_id)
    question = get_object_or_404(Question, id=question_id)
    
    sheet.questions.remove(question)
    sheet.save()
    
    return redirect('administrator_sheet', slug=sheet.slug)

# ========================= REORDER SHEET QUESTIONS ==========================

@admin_required
def reorder(request, slug):
    sheet = get_object_or_404(Sheet, slug=slug)
    questions = sheet.get_ordered_questions()
    administrator = Administrator.objects.get(id=request.user.id)
    
    parameters = {
        "administrator": administrator,
        "sheet": sheet,
        "questions": questions
    }
    
    return render(request, 'administration/sheet/reorder.html', parameters)

# ========================= UPDATE SHEET ORDER ==========================

@admin_required
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

@admin_required
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
@admin_required
def leaderboard(request, slug):
    
    administrator = Administrator.objects.get(id=request.user.id)
    sheet = Sheet.objects.get(slug=slug)
    
    parameters = {
        "administrator": administrator,
        "sheet": sheet,
    }
    
    return render(request, 'administration/sheet/leaderboard.html', parameters)


def sheet_leaderboard(request, slug):
    sheet = get_object_or_404(Sheet, slug=slug)
    
    # Handle different sheet types
    if sheet.sheet_type == 'MCQ':
        return _get_mcq_leaderboard(sheet)
    else:
        return _get_coding_leaderboard(sheet)

def _get_coding_leaderboard(sheet):
    """Generate leaderboard for coding type sheets"""
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

    # Get additional batch fields
    batch_fields, enrollment_data = _get_batch_enrollment_data(sheet, list(user_scores.keys()))

    # Format leaderboard data
    leaderboard = []
    for user_id, data in user_scores.items():
        user = Student.objects.get(id=user_id)
        total_score = sum(data[qid] for qid in data if isinstance(qid, int))  # Sum scores for questions
        solved_problems = len(data['solved_questions'])

        student_entry = {
            'student': {
                'id': user_id,
                'name': f"{user.first_name} {user.last_name}",
            },
            'total_score': total_score,
            'earliest_submission': data['earliest_submission'],
            'solved_problems': solved_problems,
        }
        
        # Add additional enrollment data
        if user_id in enrollment_data:
            student_entry['additional_data'] = enrollment_data[user_id]
        
        leaderboard.append(student_entry)

    leaderboard.sort(key=lambda x: (-x['total_score'], x['earliest_submission']))
    return JsonResponse({
        'leaderboard': leaderboard,
        'additional_fields': batch_fields
    })

def _get_mcq_leaderboard(sheet):
    """Generate leaderboard for MCQ type sheets"""
    total_questions = sheet.mcq_questions.all()

    # Fetch all MCQ submissions for the sheet
    submissions = MCQSubmission.objects.filter(
        question__in=total_questions
    )

    # Dictionary to store scores for each user
    user_scores = {}
    for submission in submissions:
        user_id = submission.student.id
        question_id = submission.question.id

        # Initialize user entry if not present
        if user_id not in user_scores:
            user_scores[user_id] = {
                'total_score': 0,
                'earliest_submission': submission.submitted_at,
                'solved_questions': set(),
                'correct_answers': set(),
            }

        # For MCQ, each correct answer gets 1 point
        if submission.is_correct:
            user_scores[user_id]['correct_answers'].add(question_id)
            user_scores[user_id]['solved_questions'].add(question_id)

        # Update earliest submission
        user_scores[user_id]['earliest_submission'] = min(
            user_scores[user_id]['earliest_submission'], submission.submitted_at
        )

    # Get additional batch fields
    batch_fields, enrollment_data = _get_batch_enrollment_data(sheet, list(user_scores.keys()))

    # Format leaderboard data
    leaderboard = []
    for user_id, data in user_scores.items():
        user = Student.objects.get(id=user_id)
        total_score = len(data['correct_answers'])  # Number of correct answers
        solved_problems = len(data['solved_questions'])  # Total attempted

        student_entry = {
            'student': {
                'id': user_id,
                'name': f"{user.first_name} {user.last_name}",
            },
            'total_score': total_score,
            'earliest_submission': data['earliest_submission'],
            'solved_problems': solved_problems,
        }
        
        # Add additional enrollment data
        if user_id in enrollment_data:
            student_entry['additional_data'] = enrollment_data[user_id]
        
        leaderboard.append(student_entry)

    leaderboard.sort(key=lambda x: (-x['total_score'], x['earliest_submission']))
    return JsonResponse({
        'leaderboard': leaderboard,
        'additional_fields': batch_fields
    })

# =========================================== DOWNLOAD LEADERBOARD =============================
import pandas as pd
from django.http import HttpResponse
from django.utils.timezone import make_naive

@admin_required
def download_leaderboard_excel(request, slug):
    sheet = get_object_or_404(Sheet, slug=slug)
    
    # Handle different sheet types
    if sheet.sheet_type == 'MCQ':
        return _download_mcq_leaderboard_excel(sheet, slug)
    else:
        return _download_coding_leaderboard_excel(sheet, slug)

def _get_batch_enrollment_data(sheet, user_ids):
    """Get additional batch enrollment data for students"""
    # Get all batches associated with this sheet
    sheet_batches = sheet.batches.all()
    
    # Collect all required fields from all batches
    all_required_fields = set()
    for batch in sheet_batches:
        if batch.required_fields:
            all_required_fields.update(batch.required_fields)
    
    # Get enrollment data for all students in the leaderboard
    enrollment_data = {}
    if all_required_fields and user_ids:
        enrollments = EnrollmentRequest.objects.filter(
            student_id__in=user_ids,
            batch__in=sheet_batches,
            status='Accepted'
        ).select_related('student', 'batch')
        
        for enrollment in enrollments:
            user_id = enrollment.student.id
            if user_id not in enrollment_data:
                enrollment_data[user_id] = {}
            
            # Merge additional data from all enrollments
            if enrollment.additional_data:
                enrollment_data[user_id].update(enrollment.additional_data)
    
    return list(all_required_fields), enrollment_data

def _download_coding_leaderboard_excel(sheet, slug):
    """Generate Excel leaderboard for coding type sheets"""
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

    # Get additional batch fields
    batch_fields, enrollment_data = _get_batch_enrollment_data(sheet, list(user_scores.keys()))

    # Format leaderboard data for DataFrame
    leaderboard = []
    for user_id, data in user_scores.items():
        user = Student.objects.get(id=user_id)
        total_score = sum(data[qid] for qid in data if isinstance(qid, int))  # Sum scores for questions
        solved_problems = len(data['solved_questions'])

        # Convert timezone-aware datetime to naive
        earliest_submission_naive = make_naive(data['earliest_submission'])

        row_data = {
            'Student ID': user_id,
            'Student Name': f"{user.first_name} {user.last_name}",
            'Email': user.email,
            'Total Score': total_score,
            'Earliest Submission': earliest_submission_naive,
            'Solved Problems': solved_problems,
        }
        
        # Add additional enrollment fields
        if user_id in enrollment_data:
            for field in batch_fields:
                row_data[field] = enrollment_data[user_id].get(field, '')
        else:
            for field in batch_fields:
                row_data[field] = ''
        
        leaderboard.append(row_data)

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

def _download_mcq_leaderboard_excel(sheet, slug):
    """Generate Excel leaderboard for MCQ type sheets"""
    total_questions = sheet.mcq_questions.all()

    # Fetch all MCQ submissions for the sheet
    submissions = MCQSubmission.objects.filter(
        question__in=total_questions
    )

    # Dictionary to store scores for each user
    user_scores = {}
    for submission in submissions:
        user_id = submission.student.id
        question_id = submission.question.id

        # Initialize user entry if not present
        if user_id not in user_scores:
            user_scores[user_id] = {
                'total_score': 0,
                'earliest_submission': submission.submitted_at,
                'solved_questions': set(),
                'correct_answers': set(),
            }

        # For MCQ, each correct answer gets 1 point
        if submission.is_correct:
            user_scores[user_id]['correct_answers'].add(question_id)
            user_scores[user_id]['solved_questions'].add(question_id)

        # Update earliest submission
        user_scores[user_id]['earliest_submission'] = min(
            user_scores[user_id]['earliest_submission'], submission.submitted_at
        )

    # Get additional batch fields
    batch_fields, enrollment_data = _get_batch_enrollment_data(sheet, list(user_scores.keys()))

    # Format leaderboard data for DataFrame
    leaderboard = []
    for user_id, data in user_scores.items():
        user = Student.objects.get(id=user_id)
        total_score = len(data['correct_answers'])  # Number of correct answers
        solved_problems = len(data['solved_questions'])  # Total attempted

        # Convert timezone-aware datetime to naive
        earliest_submission_naive = make_naive(data['earliest_submission'])

        row_data = {
            'Student ID': user_id,
            'Student Name': f"{user.first_name} {user.last_name}",
            'Email': user.email,
            'Total Score': total_score,
            'Earliest Submission': earliest_submission_naive,
            'Solved Problems': solved_problems,
        }
        
        # Add additional enrollment fields
        if user_id in enrollment_data:
            for field in batch_fields:
                row_data[field] = enrollment_data[user_id].get(field, '')
        else:
            for field in batch_fields:
                row_data[field] = ''
        
        leaderboard.append(row_data)

    # Sort by total score (descending) and earliest submission (ascending)
    leaderboard.sort(key=lambda x: (-x['Total Score'], x['Earliest Submission']))

    # Create a DataFrame from the leaderboard data
    df = pd.DataFrame(leaderboard)

    # Generate Excel file
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="mcq_leaderboard_{slug}.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="MCQ Leaderboard")

    return response

