from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.db.models import Q
from accounts.models import Administrator, Student, Instructor
from student.models import Notification, Anonymous_Message, Feedback, Assignment, AssignmentSubmission, Course

# Helper function for instructor authorization
def is_instructor(user):
    """Check if user is an instructor"""
    return hasattr(user, 'instructor') and user.instructor is not None
from practice.models import Sheet, Submission, Question
from home.models import FlamesRegistration, FlamesCourse
from angaar_hai.custom_decorators import admin_required
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json
from django.utils import timezone
import datetime
from django.http import JsonResponse
import math


from django.utils.timezone import now
from datetime import timedelta

from practice.models import Streak

# ======================================== ADMINISTRATION ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def index(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    latest_sheet = Sheet.objects.latest('id')
    
    todays_submissions = Submission.get_todays_total_submissions()
    
    # get the total number of submissions happened today only
    # today = datetime.date.today()
    # total_submissions_today = Submission.objects.filter(submitted_at__date=today).count()
    
    # today = timezone.now().date()

    # # Filter users who logged in today
    # users_today = Student.objects.filter(last_login__date=today)

    # # Get the count of such users
    # total_users_today = users_today.count()
    
    # last_3_questions = Question.objects.order_by('-created_at')[:3]

    
    # sessions = Session.objects.filter(administrator=administrator, recorded_session_link=None).order_by("-session_time")
    
    # total_enrolled_students = Student.objects.filter(courses__administrator=administrator).distinct().count()
    # total_sessions = Session.objects.filter(administrator=administrator).count()
    
    # course = Course.objects.get(administrator=administrator)
    
    # if total_sessions == 0:
    #     total_completed_sessions_percentage = 0
    # else:
    #     total_completed_sessions_percentage = int((Session.objects.filter(administrator=administrator, is_completed=True).count() / total_sessions) * 100)
    
    parameters = {
        "administrator": administrator,
        "latest_sheet": latest_sheet,
        
        "todays_submissions": todays_submissions,
        # "total_enrolled_students": total_enrolled_students,
        # "total_sessions": total_sessions,
        # "sessions": sessions,
        # "total_completed_sessions_percentage": total_completed_sessions_percentage,
        # "course": course
    }
    
    return render(request, "administration/index.html", parameters)
    
    # last_3_questions = Question.objects.order_by('-created_at')[:3]

    
    # sessions = Session.objects.filter(administrator=administrator, recorded_session_link=None).order_by("-session_time")
    
    # total_enrolled_students = Student.objects.filter(courses__administrator=administrator).distinct().count()
    # total_sessions = Session.objects.filter(administrator=administrator).count()
    
    # course = Course.objects.get(administrator=administrator)
    
    # if total_sessions == 0:
    #     total_completed_sessions_percentage = 0
    # else:
    #     total_completed_sessions_percentage = int((Session.objects.filter(administrator=administrator, is_completed=True).count() / total_sessions) * 100)
    
    parameters = {
        "administrator": administrator,
        "latest_sheet": latest_sheet,
        # "total_enrolled_students": total_enrolled_students,
        # "total_sessions": total_sessions,
        # "sessions": sessions,
        # "total_completed_sessions_percentage": total_completed_sessions_percentage,
        # "course": course
    }
    
    return render(request, "administration/index.html", parameters)

# ================================================================================================
# ========================================= DATA WORK ============================================
# ================================================================================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def fetch_all_students(request):
    today = datetime.date.today()
    
    # Fetch query and pagination parameters
    query = request.GET.get('query', '')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    
    # Base QuerySet
    students = Student.objects.all().distinct().order_by('-id')
    
    # Apply search filter if query is present
    if query:
        students = students.filter(
            Q(id__icontains=query) |
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    # Get students with birthdays today
    students_birthday = students.filter(dob__day=today.day, dob__month=today.month)
    
    # Pagination logic
    total_students = students.count()
    total_pages = math.ceil(total_students / page_size)
    start = (page - 1) * page_size
    end = start + page_size
    
    students_paginated = students[start:end]
    
    # Prepare JSON response
    data = {
        "students": [
            {
                "id": student.id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "username": student.username,
                "email": student.email,
                "college": student.college,
                "linkedin_id": student.linkedin_id,
                "github_id": student.github_id,
                "mobile_number": student.mobile_number,
                'sparks': student.coins,
                "is_active": student.is_active,
                "profile_pic": student.profile_pic.url if student.profile_pic else None,
                
                "block_url": reverse('block_student', args=[student.id]),
                "unblock_url": reverse('unblock_student', args=[student.id]),
            }
            for student in students_paginated
        ],
        "students_birthday": [
            {
                "first_name": student.first_name,
                "last_name": student.last_name,
                "username": student.username,
                "email": student.email,
                "dob": student.dob.strftime('%Y-%m-%d'),
            }
            for student in students_birthday
        ],
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_students": total_students,
            "total_pages": total_pages,
        },
        "total_students": total_students,
    }
    
    return JsonResponse(data)

def all_students(request):
    
    # get the student count who are inactive from last 3 months
    three_months_ago = timezone.now() - timedelta(days=90)
    inactive_students = Student.objects.filter(last_login__lt=three_months_ago, is_active=True)
    
    parameters = {
        "inactive_students": inactive_students,
    }
    
    return render(request, "administration/all_students.html", parameters)


# ===================================== CHANGE STUDENT PASSWORD API =======================

@csrf_exempt
def change_password(request, student_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_password = data.get('new_password')
            student = User.objects.get(id=student_id)
            student.set_password(new_password)
            student.save()
            return JsonResponse({'success': True, 'message': 'Password changed successfully'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
# ========================================= ALL INSTRUCTORS =====================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def all_instructors(request):    
    
    administrator = Administrator.objects.get(id=request.user.id)

    instructors = Instructor.objects.all().order_by("-id")
    
    query = request.POST.get("query")
    if query:
        instructors = Instructor.objects.filter(
            Q(id__icontains=query) |
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query)
            )
    
    parameters = {
        "administrator": administrator,
        "instructors": instructors,
        "query": query
    }
    
    return render(request, "administration/all_instructors.html", parameters)

# ========================================= ADD INSTRUCTOR ============================================


@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def add_instructor(request):
    try:

        if request.method == "POST":
            username = request.POST.get("username").strip()
            password = request.POST.get("password")
            gender = request.POST.get("gender")
            first_name = request.POST.get("first_name").strip()
            last_name = request.POST.get("last_name").strip()
            email = request.POST.get("email").strip()

            if Instructor.objects.filter(username=username).exists():
                messages.error(request, "Username is already taken. Please choose a different one.")
                return redirect("add_instructor")
            
            if Instructor.objects.filter(email=email).exists():
                messages.error(request, "Email is already registered. Please use a different email.")
                return redirect("add_instructor")

            instructor = Instructor()
            instructor.username = username
            instructor.gender = gender
            instructor.first_name = first_name
            instructor.last_name = last_name
            instructor.email = email
            instructor.is_staff = True
            
            instructor.set_password(password)
            
            instructor.save()

            messages.success(request, f"Instructor {first_name} {last_name} added successfully!")
            return redirect("administrator_all_instructors") 
    

    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {str(e)}")

    return render(request, "administration/add_instructor.html")

# ========================================= FEEDBACKS ============================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def feedbacks(request):
        
    administrator = Administrator.objects.get(id=request.user.id)
    
    feedbacks = Feedback.objects.all().order_by("-id")
    
    parameters = {
        "administrator": administrator,
        "feedbacks": feedbacks
    }
    
    return render(request, "administration/feedbacks.html", parameters)

# ======================================================================================================
# ========================================= ANONYMOUS MESSAGES =========================================
# ======================================================================================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def administrator_anonymous_message(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    
    my_messages = Anonymous_Message.objects.filter(administrator=administrator)
    
    parameters = {
        "administrator": administrator,
        "my_messages": my_messages
    }
    
    return render(request, "administration/administrator_anonymous_message.html", parameters)


# ======================================== REPLY MESSAGE ==========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def reply_message(request, id):
        
    administrator = Administrator.objects.get(id=request.user.id)
    
    message = Anonymous_Message.objects.get(id=id)
    
    if request.method == "POST":
        
        message.reply = request.POST.get("reply")
        message.is_replied = True
        message.save()
        
        messages.success(request, "Message replied successfully!")
        
        return redirect("administrator_anonymous_message")
    
    parameters = {
        "administrator": administrator,
        "message": message
    }
    
    return render(request, "administration/reply_message.html", parameters)


# ======================================== EDIT REPLY ==========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def edit_reply(request, id):
        
    administrator = Administrator.objects.get(id=request.user.id)
    
    message = Anonymous_Message.objects.get(id=id)
    
    if request.method == "POST":
        
        message.reply = request.POST.get("reply")
        message.save()
        
        messages.success(request, "Reply updated successfully!")
        
        return redirect("administrator_anonymous_message")
    
    parameters = {
        "administrator": administrator,
        "message": message
    }
    
    return render(request, "administration/edit_message_reply.html", parameters)


# ==============================================================================================
# ========================================= MY PROFILE =========================================
# ==============================================================================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def administrator_profile(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    
    parameters = {
        "administrator": administrator
    }
    
    return render(request, "administration/administrator_profile.html", parameters)

# ========================================= EDIT PROFILE =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def edit_administrator_profile(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    
    if request.method == "POST":
        administrator.first_name = request.POST.get("first_name")
        administrator.last_name = request.POST.get("last_name")
        administrator.email = request.POST.get("email")
        administrator.college = request.POST.get("college")
        administrator.gender = request.POST.get("gender")
        administrator.linkedin_id = request.POST.get("linkedin_id")
        
        if request.POST.get("dob"):
            administrator.dob = request.POST.get("dob")         
        
        administrator.save()
        
        messages.success(request, "Profile updated successfully!")
        
        return redirect("administrator_profile")
    
    parameters = {
        "administrator": administrator
    }
    
    return render(request, "administration/edit_administrator_profile.html", parameters)

# ========================================= UPLOAD PROFILE =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def upload_administrator_profile(request):

    if request.method == 'POST':

        administrator = Administrator.objects.get(id=request.user.id)

        administrator.profile_pic = request.FILES['profile_pic']
        
        if administrator.profile_pic.size > 5242880:
            messages.error(request, 'Profile Picture size should be less than 5MB')
            return redirect('administrator_profile')
        
        administrator.save()

        messages.success(request, 'Profile Picture Updated Successfully')

        return redirect('administrator_profile')
    
# ========================================= CHANGE PASSWORD =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def change_administrator_password(request):
        
    administrator = Administrator.objects.get(id=request.user.id)
    
    if administrator.check_password(request.POST.get("old_password")):
        
        if request.POST.get("new_password") == request.POST.get("confirm_password"):
            
            administrator.set_password(request.POST.get("new_password"))
            administrator.save()
            
            messages.success(request, "Password changed successfully! Please login Again!")
            
            return account_logout(request)
        
        else:
            messages.error(request, "New password and confirm password do not match!")
            return redirect("administrator_profile")
    
    else:
        messages.error(request, "Old password is incorrect!")
        return redirect("administrator_profile")


# ================================================================================================
# ========================================= EXTRA WORK =========================================
# ================================================================================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def notifications(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    notifications = Notification.objects.all().order_by("-expiration_date")
    
    if request.method == "POST":
        
        try:
        
            title = request.POST.get("title")
            description = request.POST.get("description")
            type = request.POST.get("notification_type")
            expiration_date = request.POST.get("expiration_date")
            is_alert = request.POST.get("is_alert")
            is_fixed = request.POST.get("is_fixed")

            notification = Notification()
            notification.title = title
            notification.description = description
            notification.type = type
            notification.expiration_date = expiration_date
            
            
            if is_alert:
                notification.is_alert = True
            
            if is_fixed:
                notification.is_fixed = True
            
            notification.save()
        
        except:
            messages.error(request, "An error occurred while sending notification!")
            return redirect("administrator_notifications")
        
        messages.success(request, "Notification sent successfully!")
        
        return redirect("administrator_notifications")
    
    parameters = {
        "administrator": administrator,
        "notifications": notifications
    }
    
    return render(request, "administration/notifications.html", parameters)


# ======================================== DELETE NOTIFICATION ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def delete_notification(request, id):
    
    notification = Notification.objects.get(id=id)
    notification.delete()
    
    messages.success(request, "Notification deleted successfully!")
    
    return redirect("administrator_notifications")


# ======================================== EDIT NOTIFICATION ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def edit_notification(request, id):
    
    administrator = Administrator.objects.get(id=request.user.id)
    
    notification = Notification.objects.get(id=id)
    
    if request.method == "POST":
        
        notification.title = request.POST.get("title")
        notification.description = request.POST.get("description")
        notification.type = request.POST.get("notification_type")
        notification.expiration_date = request.POST.get("expiration_date")
        
        if request.POST.get("is_alert"):
            notification.is_alert = True
        else:
            notification.is_alert = False
        
        if request.POST.get("is_fixed"):
            notification.is_fixed = True
        else:
            notification.is_fixed = False
        
        notification.save()
        
        messages.success(request, "Notification updated successfully!")
        
        return redirect("administrator_notifications")
    
    parameters = {
        "administrator": administrator,
        "notification": notification
    }
    
    return render(request, "administration/edit_notification.html", parameters)


# ========================================= VIEW STUDENT PROFILE =====================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def view_student_profile(request, id):
    parameters = {
        "student": Student.objects.get(id=id)
    }
    return render(request, "administration/view_student_profile.html", parameters)

@login_required(login_url='login')
def fetch_view_student_profile(request,id):

    student = Student.objects.get(id=id)
    streak = Streak.objects.filter(user=student).first()
    submissions = Submission.objects.filter(user=student).order_by("-id")[:10]
    enrolled_batches = student.batches.all().order_by("-id")

    # parameters = {
    #     "student": student,
    #     "streak": streak,
    #     "submissions": submissions,
    #     "enrolled_batches": enrolled_batches
    # }

    data = {
            "id": student.id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "username": student.username,
            "email": student.email,
            "college": student.college,
            "linkedin_id": student.linkedin_id,
            "github_id": student.github_id,
            "mobile_number": student.mobile_number,
            "sparks": student.coins,
            "is_active": student.is_active,
            "profile_pic": student.profile_pic.url if student.profile_pic else None,
            "dob": student.dob.strftime('%d-%m-%Y') if student.dob else None,
            "streak": {
                "current_streak": streak.current_streak if streak else 0,
                "last_submission_date": streak.last_submission_date.strftime('%d-%m-%Y') if streak and streak.last_submission_date else None,
            },
            "recent_submissions": [
                {
                    "id": submission.id,
                    "question": submission.question.title,
                    "score": submission.score,
                    "submitted_at": submission.submitted_at.strftime('%d-%m-%Y %H:%M:%S'),
                    "status": submission.status,
                    "code": submission.code
                }
                for submission in submissions
            ],
            "enrolled_batches": [
                {
                    "id": batch.id,
                    "slug": batch.slug
                }
                for batch in enrolled_batches
            ] if enrolled_batches else {},
    }
    
    return JsonResponse({"student": data})


def get_user_stats(request):
    """Get user statistics for the admin dashboard"""
    if request.method == 'GET':
        # Get today's date range
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timezone.timedelta(days=1)
        
        # Query for new user registrations today
        users_registered_today = Student.objects.filter(date_joined__gte=today_start, date_joined__lt=today_end).count()
        
        # Query for users who logged in today
        users_logged_in_today = Student.objects.filter(last_login__gte=today_start, last_login__lt=today_end).count()
        
        # Query for students who has their birthday today
        students_birthday_today = Student.objects.filter(dob__day=today_start.day, dob__month=today_start.month)
        
        # Query for total flames registrations
        total_flames_registrations = FlamesRegistration.objects.all().count()
        flames_registered_today = FlamesRegistration.objects.filter(created_at__gte=today_start, created_at__lt=today_end).count()

        # Format students birthday data
        birthday_data = []
        for student in students_birthday_today:
            birthday_data.append({
                'first_name': student.first_name,
                'last_name': student.last_name,
            })

        # Return the data as JSON
        return JsonResponse({
            'users_registered_today': users_registered_today,
            'users_logged_in_today': users_logged_in_today,
            'total_flames_registrations': total_flames_registrations,
            'flames_registered_today': flames_registered_today,
            'students_birthday_today': birthday_data
        })
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
