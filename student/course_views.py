from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from home.models import FlamesCourse, FlamesRegistration, FlamesTeam, FlamesTeamMember, ReferralCode
from django.http import JsonResponse

@login_required
def course_detail(request, slug):
    """
    Display detailed information about a specific F.L.A.M.E.S course
    """
    course = get_object_or_404(FlamesCourse, slug=slug, is_active=True)
    
    # Check if the user has already registered for this course
    existing_registration = FlamesRegistration.objects.filter(
        user=request.user.student,
        course=course
    ).first()
    
    context = {
        'course': course,
        'already_registered': existing_registration is not None,
        'active_tab': 'flames'
    }
    
    return render(request, 'student/course_detail.html', context)

@login_required
def student_flames_register(request, slug):
    """
    Handle registration for a F.L.A.M.E.S course by a logged-in student
    """
    course = get_object_or_404(FlamesCourse, slug=slug, is_active=True)
    
    # Check if the user has already registered for this course
    existing_registration = FlamesRegistration.objects.filter(
        user=request.user.student,
        course=course
    ).first()
    
    if existing_registration:
        messages.warning(request, f"You have already registered for {course.title}.")
        return redirect('student_flames')
    
    if request.method == 'POST':
        # Get form data
        registration_mode = request.POST.get('registration_mode')
        year = request.POST.get('year')
        message = request.POST.get('message')
        referral_code_text = request.POST.get('referral_code')
        
        # Get referral code if provided
        referral_code = None
        if referral_code_text:
            referral_code = ReferralCode.objects.filter(code=referral_code_text, is_active=True).first()
        
        # Create the registration
        registration = FlamesRegistration(
            user=request.user.student,
            course=course,
            year=year,
            message=message,
            registration_mode=registration_mode,
            referral_code=referral_code
        )
        
        # Save registration to calculate prices
        registration.save()
        
        # Handle team registration
        if registration_mode == 'TEAM':
            team_name = request.POST.get('team_name')
            team_member_count = int(request.POST.get('team_member_count', 1))
            
            # Create the team
            team = FlamesTeam.objects.create(
                name=team_name,
                team_leader=request.user,
                course=course
            )
            
            # Link the registration to the team
            registration.team = team
            registration.save()
            
            # Add the user as the first team member (team leader)
            FlamesTeamMember.objects.create(
                team=team,
                member=request.user.student,
                is_leader=True
            )
            
            # Add additional team members
            for i in range(1, team_member_count):
                member_username = request.POST.get(f'team_member_username_{i}')
                
                if member_username:
                    # Get the student account for this username
                    from accounts.models import Student
                    member_student = Student.objects.filter(username=member_username).first()
                    
                    if member_student:
                        # Create team member with the student's information
                        FlamesTeamMember.objects.create(
                            team=team,
                            member=member_student
                        )
            
            messages.success(request, f"Team '{team_name}' has been registered for {course.title} successfully!")
        else:
            # Solo registration
            messages.success(request, f"You have been registered for {course.title} successfully!")
        
        return redirect('student_flames')
    
    context = {
        'course': course,
        'active_tab': 'flames'
    }
    
    return render(request, 'student/flames_register.html', context)

def verify_referral_code(request, code):
    """
    API endpoint to verify a referral code and return discount information
    """
    referral = ReferralCode.objects.filter(code=code, is_active=True).first()
    
    if referral:
        return JsonResponse({
            'valid': True,
            'discount_amount': float(referral.discount_amount),
            'referral_type': referral.referral_type
        })
    else:
        return JsonResponse({'valid': False})
