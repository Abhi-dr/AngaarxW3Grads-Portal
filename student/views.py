from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from datetime import datetime, timedelta


# Phase 2: Student/Instructor are proxy models on the same table as CustomUser.
# request.user IS already a CustomUser — all fields (coins, dob, role, etc.) are on it directly.
# We still import Student for queryset filtering where it makes the intent clear.
from accounts.models import CustomUser
from student.models import Notification, Anonymous_Message, Feedback, Assignment, AssignmentSubmission, Course
from .event_models import Event, CertificateTemplate, Certificate
from practice.models import POD, Submission, Batch, Question, Sheet, Streak
from home.models import Alumni, ReferralCode
from django.template import engines, Template, Context
from weasyprint import HTML
from django.http import HttpResponse
from django.db.models import Max, Sum

# ========================================= DASHBOARD =========================================


# def get_user_scores_by_question(user):
#     scores = (
#         Submission.objects
#         .filter(user=user)
#         .values('question__id', 'question__title')
#         .annotate(max_score=Max('score'))
#     )
#     return {entry['question__title']: entry['max_score'] for entry in scores}

@login_required(login_url="login")
def dashboard(request):
    
    notifications = Notification.objects.filter(
        expiration_date__gt=timezone.now(),
        is_alert=True,
    ).exclude(title__startswith='Approval Request:')
    student = request.user
    
    # Get enrolled batches for the student
    enrolled_batches = Batch.objects.filter(
        enrollment_requests__student=student,
        enrollment_requests__status='Accepted'
    )
    
    # Get all sheets from enrolled batches
    enrolled_sheets = Sheet.objects.filter(
        batches__in=enrolled_batches,
        is_approved=True,
        is_enabled=True
    ).distinct()
    
    # Calculate sheet statistics based on questions solved
    total_questions_in_sheets = 0
    total_questions_solved_in_sheets = 0
    
    # Get next questions from enrolled sheets
    next_questions = []
    
    for sheet in enrolled_sheets:
        # Get all enabled questions in this sheet
        enabled_questions = sheet.get_enabled_questions_for_user(student)
        sheet_total_questions = len(enabled_questions)
        total_questions_in_sheets += sheet_total_questions
        
        if sheet.sheet_type == "MCQ":
            # For MCQ sheets, count answered questions
            from practice.models import MCQSubmission
            answered_questions_count = MCQSubmission.objects.filter(
                student=student,
                question__in=enabled_questions
            ).values('question').distinct().count()
            total_questions_solved_in_sheets += answered_questions_count
        else:
            # For coding sheets, count solved questions
            solved_questions_count = Submission.objects.filter(
                user=student,
                question__in=enabled_questions,
                status='Accepted'
            ).values('question').distinct().count()
            total_questions_solved_in_sheets += solved_questions_count
        
        # Get next question from this sheet
        if sheet.sheet_type == "MCQ":
            # For MCQ sheets, find the first unanswered question
            answered_questions = MCQSubmission.objects.filter(
                student=student,
                question__in=enabled_questions
            ).values_list('question_id', flat=True)
            
            for question in enabled_questions:
                if question.id not in answered_questions:
                    next_questions.append({
                        'question': question,
                        'sheet': sheet,
                        'type': 'MCQ'
                    })
                    break
        else:
            # For coding sheets, find the first unsolved question
            solved_questions = Submission.objects.filter(
                user=student,
                question__in=enabled_questions,
                status='Accepted'
            ).values_list('question_id', flat=True)
            
            for question in enabled_questions:
                if question.id not in solved_questions:
                    next_questions.append({
                        'question': question,
                        'sheet': sheet,
                        'type': 'Coding'
                    })
                    break
    
    # Calculate overall statistics based on questions
    questions_completion_percentage = int((total_questions_solved_in_sheets / total_questions_in_sheets) * 100) if total_questions_in_sheets > 0 else 0
    questions_left = total_questions_in_sheets - total_questions_solved_in_sheets
    total_sheets = enrolled_sheets.count()
    
    # Get today's POD from enrolled batches
    pod = None
    if enrolled_batches.exists():
        pod = POD.objects.filter(
            batch__in=enrolled_batches,
            date=datetime.now().date()
        ).first()
    
    # Check birthday
    # WHY: Old code tried getattr(student, 'student', None) — that was the MTI reverse accessor.
    # Now request.user IS CustomUser, so .dob is a direct field on it.
    is_birthday = False
    try:
        dob = request.user.dob   # directly on CustomUser — no proxy lookup needed
        if dob and dob.day == timezone.now().day and dob.month == timezone.now().month:
            is_birthday = True
    except Exception as e:
        print(f"Error checking birthday: {e}")

    parameters = {
        "notifications": notifications,
        "is_birthday": is_birthday,
        "total_sheets": total_sheets,
        "total_questions_in_sheets": total_questions_in_sheets,
        "total_questions_solved_in_sheets": total_questions_solved_in_sheets,
        "questions_completion_percentage": questions_completion_percentage,
        "questions_left": questions_left,
        "pod": pod,
        "next_questions": next_questions[:3],  # Limit to 3 questions
        "enrolled_sheets": enrolled_sheets,
    }
    
    # Check if the student's email is in the email list of Alumnis as well
    alumni = Alumni.objects.filter(email=request.user.email).first()
    if alumni:
        referral_code = ReferralCode.objects.filter(alumni=alumni).first()
        parameters['alumni'] = alumni
        parameters['referral_code'] = referral_code
    
    return render(request, "student/index.html", parameters)


# ========================================= NOTIFICATIONS =========================================

@login_required(login_url="login")
def notifications(request):
    
    notifications = Notification.objects.exclude(
        title__startswith='Approval Request:'
    ).order_by("-expiration_date")
    
    parameters = {
        "notifications": notifications
    }
    
    return render(request, "student/notifications.html", parameters)


# ========================================= ANONYMOUS MESSAGES =========================================

@login_required(login_url="login")
def anonymous_message(request):
    
    # WHY request.user not request.user.student:
    # CustomUser IS the student now — the FK on Anonymous_Message points to CustomUser directly.
    my_messages = Anonymous_Message.objects.filter(student=request.user)
    
    parameters = {
        "my_messages": my_messages
    }
    
    return render(request, "student/anonymous_message.html", parameters)


# ======================================= NEW MESSAGE ==================================================

@login_required(login_url="login")
def new_message(request):

    # request.user.courses: the ManyToMany 'courses' field is on CustomUser directly.
    # CustomUser.objects.filter() still works — Instructor is a proxy of CustomUser.
    courses = request.user.courses.all()
    my_instructors = CustomUser.objects.filter(course__in=courses).distinct()

    if request.method == "POST":
        instructor_id = request.POST.get("instructor")
        message = request.POST.get("message")

        instructor = CustomUser.objects.get(id=instructor_id)

        if Anonymous_Message.objects.filter(student=request.user, instructor=instructor, is_replied=False).exists():
            messages.error(request, "You have already sent a message to this instructor! Wait until they reply!")
            return redirect("anonymous_message")

        Anonymous_Message.objects.create(
            student=request.user,
            instructor=instructor,
            message=message
        )
        
        messages.success(request, "Message sent successfully!")
        
        return redirect("anonymous_message")  
    
    parameters = {
        "my_instructors": my_instructors
    }
    
    return render(request, "student/new_message.html", parameters)


# =========================================== RANDOM QUESTION GENERATOR ================================

@login_required(login_url="login")
def get_random_question(request):
    
    # request.user IS the CustomUser — pass it directly. All Question/Submission FKs point to it.
    student = request.user
    
    # Updated logic: Only include questions from practice sheets (not part of any batch)
    question = Question.objects.filter(
        Q(sheets__batches__isnull=True),  # Questions in sheets that are not part of any batch (practice sheets)
        is_approved=True,
        parent_id=-1
    ).exclude(
        id__in=Submission.objects.filter(
            user=request.user, 
            verdict="Accepted"
        ).values('question').distinct()
    ).distinct().order_by("?").first()
    
    if not question:
        messages.error(request, "No questions available!")
        return redirect("student")    
    
    try:
        if question.is_solved_by_user(student):
            return get_random_question(request)
    
    except RecursionError:
        messages.warning(request, "No questions available! Will be available soon!")
        return redirect("student")
        
        
    return redirect("problem", slug=question.slug)    



# ==============================================================================================
# ========================================= MY PROFILE =========================================
# ==============================================================================================

@login_required(login_url="login")
def my_profile(request):
    # Minimal view - data will be fetched via API
    return render(request, "student/my_profile.html")

# ========================================= EDIT PROFILE =========================================

@login_required(login_url="login")
def edit_profile(request):
    # Minimal view - data will be fetched and updated via API
    return render(request, "student/edit_profile.html")

# ========================================= UPLOAD PROFILE =========================================

@login_required(login_url="login")
def upload_profile(request):
    # This view is now deprecated - using API endpoint instead
    # Kept for backward compatibility
    return redirect('edit_profile')
    
# ========================================= CHANGE PASSWORD =========================================

@login_required(login_url="login")
def change_password(request):
        
    # CustomUser has set_password(), check_password(), is_changed_password directly.
    student = request.user
    
    old_password = request.POST.get("old_password")
    new_password = request.POST.get("new_password")
    confirm_password = request.POST.get("confirm_password")
    
    if student.check_password(old_password):
        
        if new_password == confirm_password and old_password != new_password:
            
            student.set_password(new_password)
            student.is_changed_password = True
            student.save()
            
            messages.success(request, "Password changed successfully! Please login Again!")
            
            return account_logout(request)
        
        elif old_password == new_password:
            messages.error(request, "New password should be different from old password!")
            return redirect("my_profile")
        
        else:
            messages.error(request, "New password and confirm password do not match!")
            return redirect("my_profile")
    
    else:
        messages.error(request, "Old password is incorrect!")
        return redirect("my_profile")

# ========================================= DELETE ACCOUNT =========================================


@login_required(login_url="login")
def delete_account(request):
    # CustomUser — calling student.delete() deletes the CustomUser row (hard delete).
    student = request.user
    
    if request.method == "POST":
    
        # Get the username from the form input (submitted via POST)
        username_input = request.POST.get("username", "").strip()

        # Check if the entered username matches the logged-in user's username
        if username_input == request.user.username:
            # If the username matches, delete the account
            student.delete()
            messages.success(request, "Account deleted successfully!")
            return account_logout(request)  # Log out the user after account deletion

        else:
            # If the username does not match, show an error message
            messages.error(request, "Username is incorrect!")
            return redirect("my_profile")  # Redirect back to the profile page

# ========================================= FEEDBACK =========================================

@login_required(login_url="login")
def feedback(request):
    
    if request.method == "POST":
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        
        Feedback.objects.create(
            student=request.user,  # FK on Feedback points to CustomUser (rewired in Phase 1)
            subject=subject,
            message=message
        )
        
        messages.success(request, "Feedback sent successfully!")
        
        return redirect("feedback")
    
    return render(request, "student/feedback.html")


# ========================================= LEVELLER =====================================

@login_required(login_url="login")
def leveller(request):
    return render(request, "student/leveller.html")

# ============================================ RESTORE STREAK =======================================

def restore_streak(request):
    if request.method == 'POST' and request.user.is_authenticated:
        student = request.user  # CustomUser — Streak FK points to it, coins field is direct
        streak = Streak.get_user_streak(student)
        
        # Check if streak can be restored using the model method
        if not streak.can_restore_streak():
            return JsonResponse({'status': 'error', 'message': 'Streak cannot be restored. You can only restore if you missed exactly 1 day.'})
        
        if student.coins >= 50:
            student.coins -= 50
            student.save()
            
            # Use the model's restore_streak method
            if streak.restore_streak():
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Streak restored successfully!',
                    'current_streak': streak.current_streak,
                    'coins_remaining': student.coins
                })
            else:
                # Refund coins if restore failed
                student.coins += 50
                student.save()
                return JsonResponse({'status': 'error', 'message': 'Failed to restore streak.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Not enough coins to restore streak. You need 50 coins.'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


# ============================================ TOTAL SCORE ==========================================

def calculate_total_user_score(user):
    total_score = (
        Submission.objects
        .filter(user=user)
        .values('question')  # Group by question
        .annotate(max_score=Max('score'))  # Take max score per question
        .aggregate(total_score=Sum('max_score'))  # Sum all max scores
    )
    
    # user_scores = get_user_scores_by_question(user)

    return total_score['total_score'] or 0


# ========================================= MY REFERRALS =========================================

@login_required
def my_referrals(request):
    """
    View to display registrations made using alumni's referral code.
    Alumni status is determined by matching email addresses.
    """
    # Check if the logged-in user is an alumni
    alumni = Alumni.objects.filter(email=request.user.email).first()
    
    if not alumni:
        messages.warning(request, "You don't have alumni status.")
        return redirect('student')
    
    # Get the referral code for this alumni
    referral_code = ReferralCode.objects.filter(alumni=alumni).first()
    
    if not referral_code:
        messages.warning(request, "You don't have a referral code yet.")
        return redirect('student')
    
    # Get all registrations that used this referral code
    from home.models import FlamesRegistration
    registrations = FlamesRegistration.objects.filter(
        referral_code=referral_code
    ).select_related('course', 'user').order_by('-created_at')
    
    # Check which users are alumni by comparing email addresses
    for registration in registrations:
        if registration.user:
            # Check if this user is also an alumni
            registration.is_alumni = Alumni.objects.filter(email=registration.user.email).exists()
        else:
            registration.is_alumni = False
    
    # Filter registrations made by alumni
    alumni_registrations = [reg for reg in registrations if reg.is_alumni]
    
    context = {
        'referral_code': referral_code,
        'registrations': registrations,
        'alumni_registrations': alumni_registrations,
        'active_tab': 'my_referrals'
    }
    
    return render(request, 'student/my_referrals.html', context)


# ====================================== MY CERTIFICATES ================================

@login_required(login_url="login")
def my_certificates(request):

    my_certificates = Certificate.objects.filter(student=request.user).select_related('event')

    parameters = {
        'my_certificates': my_certificates,
    }

    return render(request, "student/my_certificates.html", parameters)


# ======================================= VIEW CERTIFICATE ==============================


@login_required(login_url='login')
def view_certificate(request, id):
    certificate = get_object_or_404(Certificate, id=id, student=request.user)
    
    # Pass certificate ID to template for API call
    parameters = {
        'id': id,
        'certificate': certificate,
    }

    return render(request, 'student/view_certificate.html', parameters)

