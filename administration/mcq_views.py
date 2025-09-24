from django.shortcuts import render, get_object_or_404, redirect
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.urls import reverse
from django.db import transaction
from practice.models import Sheet, MCQQuestion, MCQSubmission, QuestionImage
from django.core.paginator import Paginator


@login_required(login_url='login')
def administrator_add_new_mcq_question(request, sheet_slug):
    sheet = get_object_or_404(Sheet, slug=sheet_slug)

    if sheet.sheet_type != "MCQ":
        messages.error(request, 'This is not an MCQ sheet.')
        return redirect('administrator_sheet', slug=sheet.slug)

    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        option_a = request.POST.get('option_a')
        option_b = request.POST.get('option_b')
        option_c = request.POST.get('option_c')
        option_d = request.POST.get('option_d')
        correct_option = request.POST.get('correct_option')
        explanation = request.POST.get('explanation')
        tags = request.POST.get('tags')
        difficulty_level = request.POST.get('difficulty_level')

        if not all([question_text, option_a, option_b, option_c, option_d, correct_option, difficulty_level]):
            messages.error(request, 'Please fill out all required fields.')
            return render(request, 'administration/batch/mcq/add_mcq_question.html', {'sheet': sheet})

        # Create the question first
        new_mcq_question = MCQQuestion.objects.create(
            sheet=sheet,
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_option,
            explanation=explanation,
            tags=tags,
            difficulty_level=difficulty_level,
            is_approved=True
        )

        # ==> HANDLE IMAGE UPLOADS <==
        images = request.FILES.getlist('images')
        captions = request.POST.getlist('captions')

        # Use zip to pair each image with its corresponding caption
        for image, caption in zip(images, captions):
            # We only create an image record if a file was actually uploaded
            if image:
                QuestionImage.objects.create(
                    image=image,
                    caption=caption,
                    content_object=new_mcq_question  # This links the image to the question
                )
        
        messages.success(request, 'New MCQ question and its images were added successfully!')
        return redirect('administrator_sheet', slug=sheet.slug)

    context = {
        'sheet': sheet
    }
    return render(request, 'administration/batch/mcq/add_mcq_question.html', context)


# ============================= EDIT MCQ QUESTION =============================

@login_required(login_url='login')
def administrator_edit_mcq_question(request, question_id):
    question = get_object_or_404(MCQQuestion, id=question_id)

    if request.method == 'POST':
        # 1. Update the main question text fields
        question.question_text = request.POST.get('question_text')
        question.option_a = request.POST.get('option_a')
        question.option_b = request.POST.get('option_b')
        question.option_c = request.POST.get('option_c')
        question.option_d = request.POST.get('option_d')
        question.correct_option = request.POST.get('correct_option')
        question.difficulty_level = request.POST.get('difficulty_level')
        question.explanation = request.POST.get('explanation')
        question.tags = request.POST.get('tags')
        question.save() # Save text changes first

        # 2. Handle image deletions
        delete_ids = request.POST.getlist('delete_images')
        if delete_ids:
            QuestionImage.objects.filter(id__in=delete_ids).delete()
            messages.info(request, f'Successfully deleted {len(delete_ids)} image(s).')

        # 3. Handle caption updates for existing images
        for image in question.images.all():
            new_caption = request.POST.get(f'caption_{image.id}')
            if new_caption is not None and image.caption != new_caption:
                image.caption = new_caption
                image.save()

        # 4. Handle new image uploads
        new_images = request.FILES.getlist('new_images')
        new_captions = request.POST.getlist('new_captions')

        for image_file, caption_text in zip(new_images, new_captions):
            if image_file:
                QuestionImage.objects.create(
                    image=image_file,
                    caption=caption_text,
                    content_object=question
                )

        messages.success(request, 'The MCQ question has been updated successfully!')
        return redirect('administrator_sheet', slug=question.sheet.slug)

    context = {
        'question': question
    }
    return render(request, 'administration/batch/mcq/edit_mcq_question.html', context)

# ============================= DELETE MCQ QUESTION =============================

@login_required(login_url='login')
def delete_mcq_question(request, question_id):
    question = get_object_or_404(MCQQuestion, id=question_id)
    sheet_slug = question.sheet.slug
    question.delete()
    messages.success(request, 'MCQ question deleted successfully.')
    return redirect('administrator_sheet', slug=sheet_slug)

# ============================= VIEW MCQ SUBMISSIONS =============================

def administrator_view_mcq_submissions(request, sheet_slug, question_slug):
    """
    Displays all submissions for a specific MCQ question with statistics and pagination.
    """
    # 1. Fetch the question object
    question = get_object_or_404(MCQQuestion, slug=question_slug)

    # 2. Get all submissions, ordering by the most recent first
    # Use select_related to efficiently fetch student data and avoid extra database hits
    all_submissions = question.submissions.select_related('student').order_by('-submitted_at')

    # 3. Calculate statistics
    total_attempts = all_submissions.count()
    correct_attempts = all_submissions.filter(is_correct=True).count()
    accuracy = round((correct_attempts / total_attempts * 100), 2) if total_attempts > 0 else 0

    # 4. Set up pagination
    paginator = Paginator(all_submissions, 25)  # Show 25 submissions per page
    page_number = request.GET.get('page')
    submissions_page = paginator.get_page(page_number)

    # 5. Prepare options as a JSON string for the modal's JavaScript
    options_list = [question.option_a, question.option_b, question.option_c, question.option_d]
    options_json = json.dumps(options_list)

    context = {
        'mcq_question': question,
        'submissions': submissions_page,
        'total_attempts': total_attempts,
        'correct_attempts': correct_attempts,
        'accuracy': accuracy,
        'options_json': options_json, # Pass JSON to the template
    }
    
    return render(request, 'administration/batch/mcq/view_submissions.html', context)

# ============================= MCQ JSON IMPORT =============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@csrf_exempt
def add_mcq_question_json(request, sheet_slug):
    sheet = get_object_or_404(Sheet, slug=sheet_slug)
    
    if sheet.sheet_type != "MCQ":
        return JsonResponse({
            'status': 'error',
            'message': 'This is not an MCQ sheet.'
        })
    
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            json_data = request.POST.get("json_data")
            data = json.loads(json_data)
            
            # Ensure data is a list
            if not isinstance(data, list):
                return JsonResponse({
                    'status': 'error',
                    'message': 'JSON data must be an array of MCQ questions.'
                })
            
            if not data:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No MCQ questions found in the JSON data.'
                })
            
            # Validate each question
            required_fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'difficulty_level']
            valid_difficulty_levels = ['Easy', 'Medium', 'Hard']
            valid_correct_options = ['A', 'B', 'C', 'D']
            
            created_questions = []
            
            with transaction.atomic():
                for i, question_data in enumerate(data):
                    # Validate required fields
                    for field in required_fields:
                        if field not in question_data or not str(question_data[field]).strip():
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Question {i+1}: Required field "{field}" is missing or empty.'
                            })
                    
                    # Validate difficulty_level
                    if question_data['difficulty_level'] not in valid_difficulty_levels:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Question {i+1}: Invalid difficulty level. Must be one of: {", ".join(valid_difficulty_levels)}'
                        })
                    
                    # Validate correct_option
                    correct_option = question_data['correct_option'].upper()
                    if correct_option not in valid_correct_options:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Question {i+1}: Invalid correct option. Must be one of: A, B, C, D'
                        })
                    
                    # Create the MCQ question
                    mcq_question = MCQQuestion(
                        sheet=sheet,
                        question_text=question_data['question_text'].strip(),
                        option_a=question_data['option_a'].strip(),
                        option_b=question_data['option_b'].strip(),
                        option_c=question_data['option_c'].strip(),
                        option_d=question_data['option_d'].strip(),
                        correct_option=correct_option,
                        explanation=question_data.get('explanation', '').strip(),
                        tags=question_data.get('tags', '').strip(),
                        difficulty_level=question_data['difficulty_level'],
                        is_approved=True
                    )
                    mcq_question.save()
                    created_questions.append(mcq_question)
            
            return JsonResponse({
                'status': 'success',
                'message': f'Successfully imported {len(created_questions)} MCQ questions!',
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
                'message': f'An error occurred while importing questions: {str(e)}'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.'
    })

# ============================= TEST MCQ QUESTION =============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def administrator_test_mcq(request, question_slug):
    """
    Allows administrators to test MCQ questions before they go live.
    Similar to the test_code functionality for coding questions.
    """
    mcq_question = get_object_or_404(MCQQuestion, slug=question_slug)
    
    # Get tag list for display
    tag_list = mcq_question.tag_list() if mcq_question.tags else []
    
    context = {
        'mcq_question': mcq_question,
        'tag_list': tag_list,
        'is_admin_test': True,  # Flag to indicate this is admin testing
    }
    
    return render(request, 'administration/batch/mcq/test_mcq.html', context)

# ============================= GET NEXT MCQ QUESTION FOR TESTING =============================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def get_next_mcq_question_for_testing(request, sheet_id, current_question_id):
    """
    Get the next MCQ question in the sheet for administrator testing.
    Similar to the student version but for admin testing purposes.
    """
    sheet = get_object_or_404(Sheet, id=sheet_id)
    current_question = get_object_or_404(MCQQuestion, id=current_question_id)
    
    # Get all MCQ questions in this sheet, ordered by ID
    all_questions = sheet.mcq_questions.filter(is_approved=True).order_by('id')
    
    # Find the current question's position
    question_ids = list(all_questions.values_list('id', flat=True))
    
    try:
        current_index = question_ids.index(int(current_question_id))
        
        # Check if there's a next question
        if current_index + 1 < len(question_ids):
            next_question_id = question_ids[current_index + 1]
            next_question = MCQQuestion.objects.get(id=next_question_id)
            return redirect('administrator_test_mcq', question_slug=next_question.slug)
        else:
            # No more questions, redirect back to sheet with success message
            messages.success(request, 'You have completed testing all MCQ questions in this sheet!')
            return redirect('administrator_sheet', slug=sheet.slug)
            
    except (ValueError, MCQQuestion.DoesNotExist):
        # Current question not found or error, redirect to sheet
        messages.error(request, 'Unable to find the next question.')
        return redirect('administrator_sheet', slug=sheet.slug)
