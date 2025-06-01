from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from datetime import datetime, timedelta


from accounts.models import Student, Instructor
from student.models import Notification, Anonymous_Message, Feedback, Assignment, AssignmentSubmission, Course
from practice.models import POD, Submission, Question, Sheet, Streak
from home.models import Alumni, ReferralCode
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

    # sessions = Session.objects.filter(course__in=request.user.student.courses.all(), is_completed=False)
    # last_3_completed_sessions = [session for session in Session.objects.order_by("-session_time").filter(course__in=request.user.student.courses.all(), is_completed=True) if session.recorded_session_link is not None][:3]
    
    notifications = Notification.objects.filter(expiration_date__gt=timezone.now(), is_alert=True)
    
    # total_assignments = Assignment.objects.filter(course__in=request.user.student.courses.all()).count()
    # completed_assignments = AssignmentSubmission.objects.filter(student=request.user.student).count()
    
    # assignment_percentage = int((completed_assignments / total_assignments) * 100) if total_assignments != 0 else 0
    
    total_questions_solved = Submission.objects.filter(user=request.user.student).values('question').distinct().count()
    
    total_questions_solved_percentage = int((total_questions_solved / Question.objects.filter(is_approved=True).count()) * 100) if Question.objects.filter(is_approved=True).count() != 0 else 0
    questions_left = Question.objects.filter(is_approved=True).count() - total_questions_solved
    
    pod = POD.objects.filter(date=datetime.now().date()).first()
    
    next_three_questions = (
    Question.objects
    .filter(is_approved=True)  # Only approved questions
    .exclude(
        id__in=Submission.objects
        .filter(user=request.user.student)
        .values('question')
        .distinct()
    )  # Exclude already attempted questions
    .exclude(sheets__isnull=False)  # Exclude questions linked to any sheet
    .order_by("?")[:3]  # Randomize and limit to 3 questions
)

    
    is_birthday = False
    if request.user.student.dob:
    
        if request.user.student.dob.day == timezone.now().day and request.user.student.dob.month == timezone.now().month:
            is_birthday = True
            
    
    parameters = {
        "notifications": notifications,
        "is_birthday": is_birthday,
        "total_questions_solved": total_questions_solved,
        "total_questions_solved_percentage": total_questions_solved_percentage,
        "questions_left": questions_left,
        "pod": pod,
        "next_three_questions": next_three_questions,
        
        
        # "sessions": sessions,
        # "last_3_completed_sessions": last_3_completed_sessions,
        # "completed_assignments": completed_assignments,
        # "assignment_percentage": assignment_percentage,
        # "left_assignments": total_assignments - completed_assignments,
    }
    
        # check if the student's email is in the email list of Alumnis as well
    alumni = Alumni.objects.filter(email=request.user.email).first()
    if alumni:
        referral_code = ReferralCode.objects.filter(alumni=alumni).first()
        parameters['alumni'] = alumni
        parameters['referral_code'] = referral_code
    
    return render(request, "student/index.html", parameters)


# ========================================= NOTIFICATIONS =========================================

@login_required(login_url="login")
def notifications(request):
    
    notifications = Notification.objects.order_by("-expiration_date")
    
    parameters = {
        "notifications": notifications
    }
    
    return render(request, "student/notifications.html", parameters)


# ========================================= ANONYMOUS MESSAGES =========================================

@login_required(login_url="login")
def anonymous_message(request):
    
    my_messages = Anonymous_Message.objects.filter(student=request.user.student)
    
    parameters = {
        "my_messages": my_messages
    }
    
    return render(request, "student/anonymous_message.html", parameters)


# ======================================= NEW MESSAGE ==================================================

@login_required(login_url="login")
def new_message(request):

    courses = request.user.student.courses.all()
    my_instructors = Instructor.objects.filter(course__in=courses).distinct()
    
    if request.method == "POST":
        instructor_id = request.POST.get("instructor")
        message = request.POST.get("message")
        
        instructor = Instructor.objects.get(id=instructor_id)
        
        if Anonymous_Message.objects.filter(student=request.user.student, instructor=instructor, is_replied=False).exists():
            messages.error(request, "You have already sent a message to this instructor! Wait until they reply!")
            return redirect("anonymous_message")
        
        Anonymous_Message.objects.create(
            student=request.user.student,
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
    
    student = request.user.student
    question = Question.objects.filter(is_approved=True).exclude(id__in=Submission.objects.filter(user=request.user.student).values('question').distinct()).exclude(sheets__isnull=False).order_by("?").first()
    
    print(question)
    if not question:
        messages.error(request, "No questions available!")
        return redirect("student")    
    
    try:
        if question.is_solved_by_user(student) and question.is_solved_by_user(student):
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
    
    total_score = calculate_total_user_score(request.user)
    
    parameters = {
        "total_score": total_score
    }
    
    return render(request, "student/my_profile.html", parameters)

# ========================================= EDIT PROFILE =========================================

@login_required(login_url="login")
def edit_profile(request):
    
    # Access the student profile associated with the logged-in user
    student = request.user.student

    if request.method == "POST":
        coins_earned = 0  # Track how many coins the user earns during this update

        # First Name
        if not student.first_name and request.POST.get("first_name"):
            coins_earned += 5
        student.first_name = request.POST.get("first_name")

        # Last Name
        if not student.last_name and request.POST.get("last_name"):
            coins_earned += 5
        student.last_name = request.POST.get("last_name")

        student.email = request.POST.get("email")
        student.gender = request.POST.get("gender")

        # College
        if not student.college and request.POST.get("college"):
            coins_earned += 5
        student.college = request.POST.get("college")

        # LinkedIn
        if not student.linkedin_id and request.POST.get("linkedin_id"):
            coins_earned += 20
        student.linkedin_id = request.POST.get("linkedin_id")

        # GitHub
        if not student.github_id and request.POST.get("github_id"):
            coins_earned += 20
        student.github_id = request.POST.get("github_id")

        # Date of Birth
        if not student.dob and request.POST.get("dob"):
            coins_earned += 10
        if request.POST.get("dob"):
            student.dob = request.POST.get("dob")

        # Mobile Number
        if request.POST.get("mobile_number"):
            if request.POST.get("mobile_number").isdigit() and len(request.POST.get("mobile_number")) == 10:
                if not student.mobile_number:
                    coins_earned += 10
                student.mobile_number = request.POST.get("mobile_number")
            else:
                messages.error(request, "Invalid mobile number!")
                return redirect("edit_profile")

        # Update Coins if any new fields were set
        if coins_earned > 0:
            student.coins += coins_earned  # Assuming `coins` is a field on the student model

        student.save()

        if coins_earned > 0:
            messages.success(request, f"Profile updated successfully! You earned {coins_earned} sparks ✨")
        else:
            messages.success(request, "Profile updated successfully!")

        return redirect("my_profile")

    parameters = {
        "student": student
    }
    
    return render(request, "student/edit_profile.html", parameters)

# ========================================= UPLOAD PROFILE =========================================

@login_required(login_url="login")
def upload_profile(request):

    if request.method == 'POST':

        # Access the student profile associated with the logged-in user
        student = request.user.student

        student.profile_pic = request.FILES['profile_pic']
        
        if student.profile_pic.size > 5242880:
            messages.error(request, 'Profile Picture size should be less than 5MB')
            return redirect('my_profile')
        
        student.save()

        messages.success(request, 'Profile Picture Updated Successfully!')

        return redirect('my_profile')
    
# ========================================= CHANGE PASSWORD =========================================

@login_required(login_url="login")
def change_password(request):
        
    # Access the student profile associated with the logged-in user
    student = request.user.student
    
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
    # Access the student profile associated with the logged-in user
    student = request.user.student
    
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
            student=request.user.student,
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
        student = request.user.student
        streak = Streak.objects.filter(user=student).first()
        
        if not streak:
            return JsonResponse({'status': 'error', 'message': 'No streak found for this user.'})
        
        today = datetime.now().date()
        if streak.last_submission_date != today - timedelta(days=2):
            return JsonResponse({'status': 'error', 'message': 'Streak cannot be restored.'})
        
        if student.coins >= 50:
            student.coins -= 50
            student.save()
            
            # Store the previous streak value before resetting
            previous_streak = streak.current_streak

            # Restore the streak
            streak.last_submission_date = today - timedelta(days=1)  # Set to yesterday
            streak.current_streak = previous_streak + 1  # Increase streak by 1 (restoring it)
            streak.save()
            
            return JsonResponse({'status': 'success', 'message': 'Streak restored successfully!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Not enough coins to restore streak.'})
    
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

# =======================================================================================================
# =========================================== ASSIGNMENTS =============================================
# =======================================================================================================


@login_required(login_url="login")
def assignments(request):
    """
    Display assignments from both Course and FlamesCourse models
    """
    # Access the student profile associated with the logged-in user
    student = request.user.student
    current_time = timezone.now()
    
    # Simple approach: get all assignments regardless of course type
    all_assignments = Assignment.objects.filter(
        # Only include published and draft assignments
        status__in=['Published', 'Draft']
    ).order_by('-due_date')
    
    # Get student submissions
    submissions = AssignmentSubmission.objects.filter(student=student)
    submitted_assignment_ids = list(submissions.values_list('assignment_id', flat=True))
    
    # Create a list to hold assignments with course info
    assignments_with_info = []
    
    for assignment in all_assignments:
        # Get course information
        course_name = "Unknown Course"
        
        
        # If it's a regular course assignment
        if assignment.content_type.model == 'course':
            course = Course.objects.get(id=assignment.object_id)
            course_name = course.name
            
            # Check if student is enrolled
            if not student.courses.filter(id=course.id).exists():
                continue  # Skip this assignment if not enrolled
                
        # If it's a flames course assignment
        elif assignment.content_type.model == 'flamescourse':
            from home.models import FlamesCourse, FlamesRegistration, FlamesTeamMember
            
            # Get the course
            flames_course = FlamesCourse.objects.get(id=assignment.object_id)
            course_name = flames_course.title
            
            # Check if user is registered for this flames course
            has_access = False
            
            # Direct registration
            if FlamesRegistration.objects.filter(user=student,
                course=flames_course,
                status='Completed'
            ).exists():
                has_access = True
            
            # Team membership
            if not has_access:
                student_teams = FlamesTeamMember.objects.filter(member=student)
                if student_teams.exists() and FlamesRegistration.objects.filter(
                    team__in=[member.team for member in student_teams if member.team], 
                    course=flames_course,
                    status='Completed'
                ).exists():
                    has_access = True
            
            if not has_access:
                continue  # Skip if no access to course
        else:
            continue  # Skip unknown content types
        
        # Add course info to the assignment
        assignment.course_name = course_name
        assignment.is_submitted = assignment.id in submitted_assignment_ids
        
        # Add assignment to our list
        assignments_with_info.append(assignment)
    
    parameters = {
        "assignments": assignments_with_info,
        "student": student,
        "submitted_assignments": submitted_assignment_ids,
        "current_time": current_time
    }
    
    return render(request, "student/assignments.html", parameters)


# =========================================== SUBMIT ASSIGNMENT =============================================

@login_required(login_url="login")
def submit_assignment(request, assignment_id):
    """
    Submit assignment response in a simplified manner
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = request.user.student
    
    # Check if student can access this assignment
    can_access = False
    course_name = "Unknown Course"
    
    try:
        # Regular course assignment
        if assignment.content_type.model == 'course':
            course = Course.objects.get(id=assignment.object_id)
            course_name = course.name
            
            # Check enrollment
            if student.courses.filter(id=course.id).exists():
                can_access = True
                
        # Flames course assignment
        elif assignment.content_type.model == 'flamescourse':
            from home.models import FlamesCourse, FlamesRegistration, FlamesTeamMember
            
            flames_course = FlamesCourse.objects.get(id=assignment.object_id)
            course_name = flames_course.title
            
            # Check direct registration
            if FlamesRegistration.objects.filter(
                Q(user=student) | Q(email=student.user.email),
                course=flames_course,
                status='Completed'
            ).exists():
                can_access = True
                
            # Check team registration
            if not can_access:
                student_teams = FlamesTeamMember.objects.filter(member=student)
                team_ids = [member.team.id for member in student_teams if member.team]
                if team_ids and FlamesRegistration.objects.filter(
                    team__id__in=team_ids,
                    course=flames_course,
                    status='Completed'
                ).exists():
                    can_access = True
    except Exception as e:
        messages.error(request, f"Error accessing assignment: {str(e)}")
        return redirect('assignments')
    
    # Redirect if no access
    if not can_access:
        messages.error(request, "You do not have access to this assignment")
        return redirect('assignments')
    
    # Check if already submitted
    if AssignmentSubmission.objects.filter(assignment=assignment, student=student).exists():
        messages.error(request, "You have already submitted this assignment")
        return redirect('assignments')
    
    # Check deadline
    if assignment.due_date and assignment.due_date < timezone.now():
        if assignment.status != 'Draft':
            messages.warning(request, "The deadline for this assignment has passed, but you can still submit")
    
    if request.method == 'POST':
        submission = AssignmentSubmission(
            assignment=assignment,
            student=student,
        )
        
        # Process submission based on type
        if assignment.assignment_type == 'Coding':
            submission.submission_code = request.POST.get('submission_code')
        elif assignment.assignment_type == 'Text':
            submission.submission_text = request.POST.get('submission_text')
        elif assignment.assignment_type == 'File':
            submission.submission_file = request.FILES.get('submission_file')
        elif assignment.assignment_type == 'Image':
            submission.submission_image = request.FILES.get('submission_image')
        elif assignment.assignment_type == 'Link':
            submission.submission_link = request.POST.get('submission_link')
        
        submission.extra_info = request.POST.get('extra_info')
        
        try:
            submission.save()
            messages.success(request, "Assignment submitted successfully!")
            return redirect('assignments')
        except ValueError as e:
            messages.error(request, str(e))
    
    # Add course name to assignment for template
    assignment.course_name = course_name
    
    parameters = {
        "assignment": assignment,
        "student": student
    }
    
    return render(request, "student/submit_assignment.html", parameters)


# =========================================== VIEW SUBMISSION =============================================

@login_required(login_url="login")
def view_submission(request, assignment_id):
    """
    Display a student's submission for an assignment with simplified approach
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = request.user.student
    
    # Check if student can access this assignment
    can_access = False
    course_name = "Unknown Course"
    
    try:
        # Regular course assignment
        if assignment.content_type.model == 'course':
            course = Course.objects.get(id=assignment.object_id)
            course_name = course.name
            
            # Check enrollment
            if student.courses.filter(id=course.id).exists():
                can_access = True
                
        # Flames course assignment
        elif assignment.content_type.model == 'flamescourse':
            from home.models import FlamesCourse, FlamesRegistration, FlamesTeamMember
            
            flames_course = FlamesCourse.objects.get(id=assignment.object_id)
            course_name = flames_course.title
            
            # Check direct registration
            if FlamesRegistration.objects.filter(
                Q(user=student) | Q(email=student.user.email),
                course=flames_course,
                status='Completed'
            ).exists():
                can_access = True
                
            # Check team registration
            if not can_access:
                student_teams = FlamesTeamMember.objects.filter(member=student)
                team_ids = [member.team.id for member in student_teams if member.team]
                if team_ids and FlamesRegistration.objects.filter(
                    team__id__in=team_ids,
                    course=flames_course,
                    status='Completed'
                ).exists():
                    can_access = True
    except Exception as e:
        messages.error(request, f"Error accessing assignment: {str(e)}")
        return redirect('assignments')
    
    # Redirect if no access
    if not can_access:
        messages.error(request, "You do not have access to this assignment")
        return redirect('assignments')
    
    # Get submission
    try:
        submission = AssignmentSubmission.objects.get(assignment=assignment, student=student)
    except AssignmentSubmission.DoesNotExist:
        messages.error(request, "You haven't submitted this assignment yet")
        return redirect('assignments')
    
    # Add course name to assignment
    assignment.course_name = course_name
    
    # Check if submission was late
    is_late = False
    late_penalty = 0
    final_score = submission.score if submission.score is not None else None
    
    if submission.submission_date and assignment.due_date and submission.submission_date > assignment.due_date:
        is_late = True
        if submission.score is not None and assignment.late_penalty > 0:
            late_penalty = submission.score * (assignment.late_penalty / 100)
            final_score = submission.score - late_penalty
    
    parameters = {
        'assignment': assignment,
        'submission': submission,
        'is_late': is_late,
        'late_penalty': late_penalty,
        'final_score': final_score
    }
    
    return render(request, 'student/view_submission.html', parameters)

# =========================================== DELETE SUBMISSION =============================================

@login_required(login_url="login")
def delete_submission(request, submission_id):
    """
    Delete an assignment submission if before deadline
    """
    # Get the submission
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    assignment = submission.assignment
    
    # Verify the submission belongs to the current user
    if submission.student != request.user.student:
        messages.error(request, "You cannot delete another student's submission")
        return redirect('assignments')
        
    # Check if past deadline
    if assignment.due_date and assignment.due_date < timezone.now() and assignment.status != 'Draft':
        messages.error(request, "You cannot delete the submission after the deadline.")
        return redirect('assignments')
    
    # Delete the submission
    submission.delete()
    messages.success(request, "Submission deleted successfully.")
    
    return redirect('assignments')

