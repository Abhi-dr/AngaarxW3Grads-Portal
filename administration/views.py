from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.db.models import Q
from accounts.models import Instructor, Student
from student.models import Notification, Anonymous_Message


import datetime

# ======================================== ADMINISTRATION ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def index(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
    # sessions = Session.objects.filter(instructor=instructor, recorded_session_link=None).order_by("-session_time")
    
    # total_enrolled_students = Student.objects.filter(courses__instructor=instructor).distinct().count()
    # total_sessions = Session.objects.filter(instructor=instructor).count()
    
    # course = Course.objects.get(instructor=instructor)
    
    # if total_sessions == 0:
    #     total_completed_sessions_percentage = 0
    # else:
    #     total_completed_sessions_percentage = int((Session.objects.filter(instructor=instructor, is_completed=True).count() / total_sessions) * 100)
    
    parameters = {
        "instructor": instructor,
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
def all_students(request):
        
    instructor = Instructor.objects.get(id=request.user.id)
    
    # students = Student.objects.filter(courses__instructor=instructor).distinct()
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
        "instructor": instructor,
        "students": students,
        "students_birthday": students_birthday,
        "query": query
    }
    
    return render(request, "administration/all_students.html", parameters)


# ======================================================================================================
# ========================================= ANONYMOUS MESSAGES =========================================
# ======================================================================================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def instructor_anonymous_message(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
    my_messages = Anonymous_Message.objects.filter(instructor=instructor)
    
    parameters = {
        "instructor": instructor,
        "my_messages": my_messages
    }
    
    return render(request, "administration/instructor_anonymous_message.html", parameters)


# ======================================== REPLY MESSAGE ==========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def reply_message(request, id):
        
    instructor = Instructor.objects.get(id=request.user.id)
    
    message = Anonymous_Message.objects.get(id=id)
    
    if request.method == "POST":
        
        message.reply = request.POST.get("reply")
        message.is_replied = True
        message.save()
        
        messages.success(request, "Message replied successfully!")
        
        return redirect("instructor_anonymous_message")
    
    parameters = {
        "instructor": instructor,
        "message": message
    }
    
    return render(request, "administration/reply_message.html", parameters)


# ======================================== EDIT REPLY ==========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def edit_reply(request, id):
        
    instructor = Instructor.objects.get(id=request.user.id)
    
    message = Anonymous_Message.objects.get(id=id)
    
    if request.method == "POST":
        
        message.reply = request.POST.get("reply")
        message.save()
        
        messages.success(request, "Reply updated successfully!")
        
        return redirect("instructor_anonymous_message")
    
    parameters = {
        "instructor": instructor,
        "message": message
    }
    
    return render(request, "administration/edit_message_reply.html", parameters)


# ==============================================================================================
# ========================================= MY PROFILE =========================================
# ==============================================================================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def instructor_profile(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
    parameters = {
        "instructor": instructor
    }
    
    return render(request, "administration/instructor_profile.html", parameters)

# ========================================= EDIT PROFILE =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def edit_instructor_profile(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
    if request.method == "POST":
        instructor.first_name = request.POST.get("first_name")
        instructor.last_name = request.POST.get("last_name")
        instructor.email = request.POST.get("email")
        instructor.college = request.POST.get("college")
        instructor.gender = request.POST.get("gender")
        instructor.linkedin_id = request.POST.get("linkedin_id")
        
        if request.POST.get("dob"):
            instructor.dob = request.POST.get("dob")         
        
        instructor.save()
        
        messages.success(request, "Profile updated successfully!")
        
        return redirect("instructor_profile")
    
    parameters = {
        "instructor": instructor
    }
    
    return render(request, "administration/edit_instructor_profile.html", parameters)

# ========================================= UPLOAD PROFILE =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def upload_instructor_profile(request):

    if request.method == 'POST':

        instructor = Instructor.objects.get(id=request.user.id)

        instructor.profile_pic = request.FILES['profile_pic']
        
        if instructor.profile_pic.size > 5242880:
            messages.error(request, 'Profile Picture size should be less than 5MB')
            return redirect('instructor_profile')
        
        instructor.save()

        messages.success(request, 'Profile Picture Updated Successfully')

        return redirect('instructor_profile')
    
# ========================================= CHANGE PASSWORD =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def change_instructor_password(request):
        
    instructor = Instructor.objects.get(id=request.user.id)
    
    if instructor.check_password(request.POST.get("old_password")):
        
        if request.POST.get("new_password") == request.POST.get("confirm_password"):
            
            instructor.set_password(request.POST.get("new_password"))
            instructor.save()
            
            messages.success(request, "Password changed successfully! Please login Again!")
            
            account_logout(request)
        
        else:
            messages.error(request, "New password and confirm password do not match!")
            return redirect("instructor_profile")
    
    else:
        messages.error(request, "Old password is incorrect!")
        return redirect("instructor_profile")



# ================================================================================================
# ========================================= EXTRA WORK =========================================
# ================================================================================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def notifications(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
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
            return redirect("instructor_notifications")
        
        messages.success(request, "Notification sent successfully!")
        
        return redirect("instructor_notifications")
    
    parameters = {
        "instructor": instructor,
        "notifications": notifications
    }
    
    return render(request, "administration/notifications.html", parameters)


# ======================================== DELETE NOTIFICATION ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def delete_notification(request, id):
    
    notification = Notification.objects.get(id=id)
    notification.delete()
    
    messages.success(request, "Notification deleted successfully!")
    
    return redirect("instructor_notifications")


# ======================================== EDIT NOTIFICATION ===================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def edit_notification(request, id):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
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
        
        return redirect("instructor_notifications")
    
    parameters = {
        "instructor": instructor,
        "notification": notification
    }
    
    return render(request, "administration/edit_notification.html", parameters)


