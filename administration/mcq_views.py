from django.shortcuts import render, get_object_or_404, redirect
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from practice.models import Sheet, MCQQuestion, MCQSubmission
from django.core.paginator import Paginator



@login_required(login_url='login')
def administrator_add_new_mcq_question(request, sheet_slug):
    """
    View to add a new MCQ Question to a sheet.
    """
    sheet = get_object_or_404(Sheet, slug=sheet_slug)

    # Ensure the sheet is an MCQ type sheet
    if sheet.sheet_type != "MCQ":
        messages.error(request, 'This is not an MCQ sheet.')
        # Assuming you have a URL named 'administrator_sheet_detail'
        return redirect('administrator_sheet_detail', slug=sheet.slug)

    if request.method == 'POST':
        # Retrieve data from the form
        question_text = request.POST.get('question_text')
        option_a = request.POST.get('option_a')
        option_b = request.POST.get('option_b')
        option_c = request.POST.get('option_c')
        option_d = request.POST.get('option_d')
        correct_option = request.POST.get('correct_option')
        explanation = request.POST.get('explanation')
        tags = request.POST.get('tags')
        difficulty_level = request.POST.get('difficulty_level')

        # Basic validation to ensure required fields are not empty
        if not all([question_text, option_a, option_b, option_c, option_d, correct_option, difficulty_level]):
            messages.error(request, 'Please fill out all required fields.')
            return render(request, 'administration/batch/mcq/add_mcq_question.html', {'sheet': sheet})

        # Create and save the new MCQQuestion instance
        MCQQuestion.objects.create(
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
            is_approved=True  # Automatically approve questions added by an admin
        )

        messages.success(request, 'New MCQ question was added successfully!')
        # Redirect back to the sheet detail page
        return redirect('administrator_sheet', slug=sheet.slug)

    context = {
        'sheet': sheet
    }
    return render(request, 'administration/batch/mcq/add_mcq_question.html', context)

# ============================= EDIT MCQ QUESTION =============================

@login_required(login_url='login')
def administrator_edit_mcq_question(request, question_id):

    question = get_object_or_404(MCQQuestion, id=question_id)

    # If the form is submitted (POST request)
    if request.method == 'POST':
        # Update the question object's fields with the new data from the form
        question.question_text = request.POST.get('question_text')
        question.option_a = request.POST.get('option_a')
        question.option_b = request.POST.get('option_b')
        question.option_c = request.POST.get('option_c')
        question.option_d = request.POST.get('option_d')
        question.correct_option = request.POST.get('correct_option')
        question.difficulty_level = request.POST.get('difficulty_level')
        question.explanation = request.POST.get('explanation')
        question.tags = request.POST.get('tags')

        # Save the updated object to the database
        question.save()

        # Add a success message and redirect back to the sheet detail page
        messages.success(request, 'The MCQ question has been updated successfully!')
        return redirect('administrator_sheet', slug=question.sheet.slug)

    # If it's a GET request, just display the form pre-filled with the question's data
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
