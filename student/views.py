from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.utils import timezone
from datetime import datetime
from django.db.models import Q

from accounts.models import Student, Instructor
from student.models import Notification, Anonymous_Message, Feedback
from practice.models import POD, Submission, Question, Sheet, Streak

# ========================================= DASHBOARD =========================================

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
    
    
    next_three_questions = Question.objects.filter(is_approved=True).exclude(id__in=Submission.objects.filter(user=request.user.student).values('question').distinct()).order_by("?")[:3]
    
    is_birthday = False
    if request.user.student.dob:
    
        if request.user.student.dob.day == timezone.now().day and request.user.student.dob.month == timezone.now().month:
            is_birthday = True
            
    print(is_birthday, request.user.student.first_name)
    
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
    question = Question.objects.order_by("?").first()
    
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
    return render(request, "student/my_profile.html")

# ========================================= EDIT PROFILE =========================================

@login_required(login_url="login")
def edit_profile(request):
    
    student = Student.objects.get(id=request.user.id)
    
    if request.method == "POST":
        student.first_name = request.POST.get("first_name")
        student.last_name = request.POST.get("last_name")
        student.email = request.POST.get("email")
        student.gender = request.POST.get("gender")
        student.college = request.POST.get("college")
        student.linkedin_id = request.POST.get("linkedin_id")
        student.github_id = request.POST.get("github_id")
        
        if request.POST.get("dob"):
            student.dob = request.POST.get("dob")
            
        if request.POST.get("mobile_number"):
        
            if request.POST.get("mobile_number").isdigit() and len(request.POST.get("mobile_number")) == 10:
                student.mobile_number = request.POST.get("mobile_number")
            else:
                messages.error(request, "Invalid mobile number!")
                return redirect("edit_profile")
            
        
        student.save()
        
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

        student = Student.objects.get(id=request.user.id)

        student.profile_pic = request.FILES['profile_pic']
        
        if student.profile_pic.size > 5242880:
            messages.error(request, 'Profile Picture size should be less than 5MB')
            return redirect('my_profile')
        
        student.save()

        messages.success(request, 'Profile Picture Updated Successfully')

        return redirect('my_profile')
    
# ========================================= CHANGE PASSWORD =========================================

@login_required(login_url="login")
def change_password(request):
        
    student = Student.objects.get(id=request.user.id)
    
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

