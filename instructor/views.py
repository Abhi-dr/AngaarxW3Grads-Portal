from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.db.models import Q
from accounts.models import Instructor, Student
from student.models import Notification, Anonymous_Message, Feedback
from practice.models import Sheet, Submission, Question
import datetime


# ======================================== Instructor ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def index(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    latest_sheet = Sheet.objects.latest('id')
    
    # get the total number of submissions happened today only
    today = datetime.date.today()
    total_submissions_today = Submission.objects.filter(submitted_at__date=today).count()
    
    parameters = {
        "instructor": instructor,
        "latest_sheet": latest_sheet,
    }
    
    return render(request, "instructor/index.html", parameters)
    

# ========================================= MY PROFILE =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def instructor_profile(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
    parameters = {
        "instructor": instructor
    }
    
    return render(request, "instructor/profile/instructor_profile.html", parameters)

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
    
    return render(request, "instructor/profile/edit_instructor_profile.html", parameters)



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
            
            return account_logout(request)
        
        else:
            messages.error(request, "New password and confirm password do not match!")
            return redirect("instructor_profile")
    
    else:
        messages.error(request, "Old password is incorrect!")
        return redirect("instructor_profile")
