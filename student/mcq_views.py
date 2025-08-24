from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.utils import timezone
from datetime import datetime
from django.db.models import Q, Case, When, Value, CharField
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from django.core.paginator import Paginator

from django.db.models import Count, Min, Max

from accounts.models import Student
from student.models import Notification, Course
from practice.models import Submission, Question, Sheet, Batch,EnrollmentRequest, MCQQuestion, MCQSubmission

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@login_required
def mcq_question_view(request, sheet_slug, slug):
    """
    Display MCQ question page
    """
    mcq_question = get_object_or_404(
        MCQQuestion.objects.select_related('sheet'), 
        slug=slug, 
        is_approved=True
    )
    
    # Get student
    student = get_object_or_404(Student, id=request.user.id)
    
    # Check if sheet is active and accessible
    sheet = mcq_question.sheet
    if not sheet.is_enabled or not sheet.is_approved:
        messages.error(request, "This sheet is not accessible.")
        return redirect('practice')
    
    # Check if sheet is within time bounds (if set)
    if sheet.start_time and sheet.end_time:
        now = timezone.now()
        if not (sheet.start_time <= now <= sheet.end_time):
            messages.error(request, "This sheet is not active at the moment.")
            return redirect('practice')
    
    # Check if question is enabled for sequential sheets
    if sheet.is_sequential:
        enabled_questions = sheet.get_enabled_questions_for_user(student)
        if mcq_question not in enabled_questions:
            messages.warning(request, "You need to solve previous questions first.")
            return redirect('my_sheet', slug=sheet.slug)
    
    # Check if student has already answered this question
    previous_submission = MCQSubmission.objects.filter(
        student=student,
        question=mcq_question
    ).first()
    
    context = {
        'mcq_question': mcq_question,
        'sheet': mcq_question.sheet,
        'student': student,
        'previous_submission': previous_submission,
    }
    
    return render(request, 'student/batch/mcq/problem.html', context)



@login_required
@require_http_methods(["POST"])
def submit_mcq_answer(request, slug):
    """
    Handle MCQ answer submission
    """
    try:
        mcq_question = get_object_or_404(
            MCQQuestion.objects.select_related('sheet'), 
            slug=slug, 
            is_approved=True
        )
        
        student = get_object_or_404(Student, user=request.user)
        
        # Parse JSON data
        try:
            data = json.loads(request.body)
            selected_option = data.get('selected_option', '').upper()
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data',
                'is_correct': False
            }, status=400)
        
        # Validate selected option
        if selected_option not in ['A', 'B', 'C', 'D']:
            return JsonResponse({
                'error': 'Invalid option selected',
                'is_correct': False
            }, status=400)
        
        # Check if sheet is still accessible
        sheet = mcq_question.sheet
        if not sheet.is_enabled or not sheet.is_approved:
            return JsonResponse({
                'error': 'Sheet is not accessible',
                'is_correct': False
            }, status=403)
        
        # Check if student has already submitted for this question
        existing_submission = MCQSubmission.objects.filter(
            student=student,
            question=mcq_question
        ).first()
        
        # Determine if answer is correct
        is_correct = selected_option == mcq_question.correct_option
        
        with transaction.atomic():
            if existing_submission:
                # Update existing submission
                existing_submission.selected_option = selected_option
                existing_submission.is_correct = is_correct
                existing_submission.submitted_at = timezone.now()
                existing_submission.save()
                submission = existing_submission
            else:
                # Create new submission
                submission = MCQSubmission.objects.create(
                    student=student,
                    question=mcq_question,
                    selected_option=selected_option,
                    is_correct=is_correct
                )
        
        response_data = {
            'is_correct': is_correct,
            'correct_option': mcq_question.correct_option,
            'selected_option': selected_option,
            'explanation': mcq_question.explanation or '',
            'submission_id': submission.id
        }
        
        if is_correct:
            response_data['message'] = 'Correct answer! Well done.'
        else:
            response_data['message'] = f'Incorrect. The correct answer is {mcq_question.correct_option}.'
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': 'An error occurred while submitting your answer',
            'is_correct': False
        }, status=500)


@login_required
def mcq_submissions(request, slug):
    """
    Display student's submissions for this MCQ question
    """
    try:
        mcq_question = get_object_or_404(
            MCQQuestion.objects.select_related('sheet'), 
            slug=slug, 
            is_approved=True
        )
        
        student = get_object_or_404(Student, user=request.user)
        
        # Get all submissions for this question by this student
        submissions = MCQSubmission.objects.filter(
            student=student,
            question=mcq_question
        ).order_by('-submitted_at')
        
        # Paginate submissions
        paginator = Paginator(submissions, 20)
        page_number = request.GET.get('page')
        page_submissions = paginator.get_page(page_number)
        
        # Get statistics
        total_attempts = submissions.count()
        correct_attempts = submissions.filter(is_correct=True).count()
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        
        context = {
            'mcq_question': mcq_question,
            'submissions': page_submissions,
            'student': student,
            'total_attempts': total_attempts,
            'correct_attempts': correct_attempts,
            'accuracy': round(accuracy, 1),
        }
        
        return render(request, 'student/mcq_submissions.html', context)
        
    except Exception as e:
        messages.error(request, "Submissions not found.")
        return redirect('practice')


@login_required
def fetch_recommended_mcq_questions(request, slug):
    """
    Fetch recommended MCQ questions based on current question
    """
    try:
        current_question = get_object_or_404(MCQQuestion, slug=slug, is_approved=True)
        
        # Get student
        student = get_object_or_404(Student, user=request.user)
        
        # Get questions from same sheet, excluding current question
        sheet_questions = MCQQuestion.objects.filter(
            sheet=current_question.sheet,
            is_approved=True
        ).exclude(id=current_question.id)
        
        # Get questions student hasn't answered correctly yet
        correctly_answered_question_ids = MCQSubmission.objects.filter(
            student=student,
            is_correct=True
        ).values_list('question_id', flat=True)
        
        unanswered_questions = sheet_questions.exclude(
            id__in=correctly_answered_question_ids
        )
        
        # If no unanswered questions in sheet, get from same difficulty level
        if not unanswered_questions.exists():
            unanswered_questions = MCQQuestion.objects.filter(
                difficulty_level=current_question.difficulty_level,
                is_approved=True
            ).exclude(
                id__in=correctly_answered_question_ids
            ).exclude(id=current_question.id)
        
        # Get tags from current question for similarity matching
        current_tags = []
        if current_question.tags:
            current_tags = [tag.strip().lower() for tag in current_question.tags.split(',')]
        
        # Score questions based on tag similarity
        recommended_questions = []
        for question in unanswered_questions[:20]:  # Limit to 20 for performance
            score = 0
            if question.tags and current_tags:
                question_tags = [tag.strip().lower() for tag in question.tags.split(',')]
                common_tags = set(current_tags).intersection(set(question_tags))
                score = len(common_tags)
            
            recommended_questions.append({
                'question': question,
                'score': score
            })
        
        # Sort by score (descending) and take top 5
        recommended_questions.sort(key=lambda x: x['score'], reverse=True)
        top_recommendations = recommended_questions[:5]
        
        # Prepare response data
        questions_data = []
        for item in top_recommendations:
            question = item['question']
            questions_data.append({
                'id': question.id,
                'slug': question.slug,
                'question_text': question.question_text,
                'difficulty_level': question.difficulty_level,
                'tags': question.tags or '',
                'sheet_name': question.sheet.name if question.sheet else ''
            })
        
        return JsonResponse({
            'questions': questions_data,
            'total_count': len(questions_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'questions': [],
            'error': 'Failed to fetch recommendations'
        })


@login_required
def render_next_mcq_question_in_sheet(request, sheet_id, question_id):
    """
    Navigate to next MCQ question in the sheet
    """
    try:
        sheet = get_object_or_404(Sheet, id=sheet_id, sheet_type="MCQ")
        current_question = get_object_or_404(MCQQuestion, id=question_id)
        
        # Get student
        student = get_object_or_404(Student, user=request.user)
        
        # Use the sheet's method to get next question
        next_question = sheet.get_next_question(current_question)
        
        if next_question:
            # Check if next question is enabled (for sequential sheets)
            if sheet.is_sequential:
                enabled_questions = sheet.get_enabled_questions_for_user(student)
                if next_question not in enabled_questions:
                    messages.warning(request, "You need to solve the current question correctly first.")
                    return redirect('mcq_question', slug=current_question.slug)
            
            return redirect('mcq_question', slug=next_question.slug)
        else:
            # No more questions in sheet
            messages.success(request, "Congratulations! You've completed all MCQ questions in this sheet.")
            return redirect('my_sheet', slug=sheet.slug)
                
    except Exception as e:
        messages.error(request, "Unable to navigate to next question.")
        return redirect('practice')


@login_required
def mcq_leaderboard(request, slug):
    """
    Display leaderboard for MCQ sheet
    """
    try:
        sheet = get_object_or_404(Sheet, slug=slug, sheet_type="MCQ", is_approved=True)
        
        # Get all students who have attempted questions in this sheet
        student_stats = []
        
        # Get all approved questions in this sheet
        sheet_questions = sheet.mcq_questions.filter(is_approved=True)
        total_questions = sheet_questions.count()
        
        if total_questions == 0:
            context = {
                'sheet': sheet,
                'student_stats': [],
                'total_questions': 0
            }
            return render(request, 'student/mcq_leaderboard.html', context)
        
        # Get all students who have made submissions
        students_with_submissions = Student.objects.filter(
            mcq_submissions__question__in=sheet_questions
        ).distinct()
        
        for student in students_with_submissions:
            correct_answers = MCQSubmission.objects.filter(
                student=student,
                question__in=sheet_questions,
                is_correct=True
            ).count()
            
            total_attempts = MCQSubmission.objects.filter(
                student=student,
                question__in=sheet_questions
            ).count()
            
            accuracy = (correct_answers / total_attempts * 100) if total_attempts > 0 else 0
            completion_rate = (correct_answers / total_questions * 100) if total_questions > 0 else 0
            
            student_stats.append({
                'student': student,
                'correct_answers': correct_answers,
                'total_attempts': total_attempts,
                'accuracy': round(accuracy, 1),
                'completion_rate': round(completion_rate, 1),
                'score': correct_answers  # Simple scoring based on correct answers
            })
        
        # Sort by score (correct answers) descending, then by accuracy
        student_stats.sort(key=lambda x: (x['score'], x['accuracy']), reverse=True)
        
        # Add rank
        for i, stat in enumerate(student_stats, 1):
            stat['rank'] = i
        
        context = {
            'sheet': sheet,
            'student_stats': student_stats,
            'total_questions': total_questions,
        }
        
        return render(request, 'student/mcq_leaderboard.html', context)
        
    except Exception as e:
        messages.error(request, "Leaderboard not found.")
        return redirect('practice')


@login_required
def mcq_sheet_progress(request, slug):
    """
    Show detailed progress for MCQ sheet
    """
    try:
        sheet = get_object_or_404(Sheet, slug=slug, sheet_type="MCQ", is_approved=True)
        student = get_object_or_404(Student, user=request.user)
        
        # Get all questions in order
        questions = sheet.get_ordered_questions()
        
        # Get student's submissions for this sheet
        submissions = MCQSubmission.objects.filter(
            student=student,
            question__in=questions
        ).select_related('question')
        
        # Create submission map for easy lookup
        submission_map = {sub.question.id: sub for sub in submissions}
        
        # Prepare question data with submission status
        question_data = []
        for question in questions:
            submission = submission_map.get(question.id)
            status = 'not_attempted'
            
            if submission:
                status = 'correct' if submission.is_correct else 'incorrect'
            
            question_data.append({
                'question': question,
                'submission': submission,
                'status': status,
                'is_enabled': question in sheet.get_enabled_questions_for_user(student) if sheet.is_sequential else True
            })
        
        # Calculate statistics
        total_questions = len(questions)
        attempted_questions = len([q for q in question_data if q['submission']])
        correct_questions = len([q for q in question_data if q['status'] == 'correct'])
        
        accuracy = (correct_questions / attempted_questions * 100) if attempted_questions > 0 else 0
        completion_rate = (correct_questions / total_questions * 100) if total_questions > 0 else 0
        
        context = {
            'sheet': sheet,
            'question_data': question_data,
            'total_questions': total_questions,
            'attempted_questions': attempted_questions,
            'correct_questions': correct_questions,
            'accuracy': round(accuracy, 1),
            'completion_rate': round(completion_rate, 1),
            'student': student,
        }
        
        return render(request, 'student/mcq_sheet_progress.html', context)
        
    except Exception as e:
        messages.error(request, "Sheet progress not found.")
        return redirect('practice')