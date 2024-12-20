from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.db.models import Q
from accounts.models import Administrator, Student, Instructor
from student.models import Notification, Anonymous_Message, Feedback
from practice.models import Sheet, Submission, Question
from angaar_hai.custom_decorators import admin_required

import datetime

# ======================================== ADMINISTRATION ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
@admin_required
def index(request):
    
    administrator = Administrator.objects.get(id=request.user.id)
    latest_sheet = Sheet.objects.latest('id')
    
    # get the total number of submissions happened today only
    today = datetime.date.today()
    total_submissions_today = Submission.objects.filter(submitted_at__date=today).count()
    print(total_submissions_today)

    
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
def all_students(request):
        
    administrator = Administrator.objects.get(id=request.user.id)
    
    # students = Student.objects.filter(courses__administrator=administrator).distinct()
    students = Student.objects.all().distinct()
    
    # fetch those students who has their birthdays today
    
    today = datetime.date.today()
    students_birthday = Student.objects.filter(dob__day=today.day, dob__month=today.month)
    
    
    query = request.POST.get("query")
    if query:
        students = Student.objects.filter(
            Q(id__icontains=query) |
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query)
            )
    
    parameters = {
        "administrator": administrator,
        "students": students,
        "students_birthday": students_birthday,
        "query": query
    }
    
    return render(request, "administration/all_students.html", parameters)

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
            
            account_logout(request)
        
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
            
            print(type)
            
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


