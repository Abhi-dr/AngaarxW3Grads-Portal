from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.contrib.contenttypes.models import ContentType


from accounts.models import Student, Instructor
from student.models import Notification, Anonymous_Message, Feedback, Assignment, AssignmentSubmission, Course, CourseRegistration
from practice.models import POD, Submission, Question, Sheet, Streak
from home.models import Alumni, ReferralCode
from django.db.models import Max, Sum


# =======================================================================================================
# ============================================== JOVAC ==================================================
# =======================================================================================================

def jovac(request, slug):
    course = get_object_or_404(Course, slug=slug)
    instructors = course.instructors.all()

    content_type = ContentType.objects.get_for_model(Course)
    
    assignments = Assignment.objects.filter(
        content_type=content_type,
        object_id=course.id
    )

    submitted_assignment_ids = AssignmentSubmission.objects.filter(
        assignment__content_type=content_type,
        assignment__object_id=course.id
        ).values_list('assignment_id', flat=True)
    

    context = {
        'course': course,
        'instructors': instructors,
        'assignments': assignments,
        "submitted_assignment_ids": submitted_assignment_ids,
    }
    return render(request, 'student/jovac/jovac.html', context)

@login_required(login_url="login")
def enroll_jovac(request, slug):
    student = request.user.student

    course = get_object_or_404(Course, slug=slug)

    existing_registration = CourseRegistration.objects.filter(student=student, course=course).first()
    if existing_registration:
        messages.info(request, f"You have already {existing_registration.status.lower()} this course.")
        return redirect('my_batches')  # or wherever you want to redirect

    # Create new course registration with status 'Pending'
    CourseRegistration.objects.create(
        student=student,
        course=course,
        status='Pending'
    )

    messages.success(request, "Your enrollment request in this JOVAC has been submitted successfully!")
    return redirect('my_batches')


# =======================================================================================================
# =========================================== ASSIGNMENTS ===============================================
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
            print("Regular Course")
            course = Course.objects.get(id=assignment.object_id)
            course_name = course.name
            
            # Check if student is enrolled
            try:
                if not student.courses.filter(id=course.id).exists():
                    continue  # Skip this assignment if not enrolled
            except Exception as e:
                print(f"Error accessing course: {e}")
                pass
        # If it's a flames course assignment
        elif assignment.content_type.model == 'flamescourse':
            from home.models import FlamesCourse, FlamesRegistration, FlamesTeamMember
            
            # Get the course
            flames_course = FlamesCourse.objects.get(id=assignment.object_id)
            course_name = flames_course.title
            
            # Check if user is registered for this flames course
            has_access = False
            
            # Direct registration
            if FlamesRegistration.objects.filter(user=student,course=flames_course,status='Completed').exists():
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
    student = Student.objects.get(id=request.user.id)
    
    # Check if student can access this assignment
    can_access = False
    course_name = "Unknown Course"
    
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
        if FlamesRegistration.objects.filter(user=student,
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
    student = Student.objects.get(id=request.user.id)
    
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
            if FlamesRegistration.objects.filter(user=student,
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
    
    
    
    parameters = {
        'assignment': assignment,
        'submission': submission,
        'is_late': is_late,
        'late_penalty': late_penalty,
        'final_score': final_score,
        "course_name": course_name,
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

