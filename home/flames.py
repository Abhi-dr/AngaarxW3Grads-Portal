from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import FlamesCourse, FlamesCourseTestimonial, FlamesRegistration, ReferralCode, FlamesTeam, FlamesTeamMember
from django.utils import timezone
from django.contrib.auth.decorators import login_required

# ===================================== FLAMES PAGE ==============================

def flames(request):
    courses = FlamesCourse.objects.filter(is_active=True)
    return render(request, "home/flames.html", {'courses': courses})

# =================================== PROGRAM DETAILS ============================

def course_detail(request, slug):
    course = get_object_or_404(FlamesCourse, slug=slug, is_active=True)
    testimonials = FlamesCourseTestimonial.objects.filter(course=course)
    
    context = {
        'course': course,
        'testimonials': testimonials,
        'learning_points': course.get_learning_points(),
    }
    
    return render(request, "home/course_detail.html", context)

# =================================== REGISTER COURSE ============================

def register_course(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        course_id = request.POST.get('course_id')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        contact_number = request.POST.get('contact_number')
        college = request.POST.get('college')
        year = request.POST.get('year')
        registration_mode = request.POST.get('registration_mode')
        referral_code = request.POST.get('referral_code')
        
        try:
            course = FlamesCourse.objects.get(id=course_id, is_active=True)
            
            # Process referral code if provided
            referral = None
            if referral_code:
                try:
                    # Check if referral code exists and is valid
                    referral = ReferralCode.objects.get(code=referral_code, is_active=True)
                    
                    # Validate referral code type matches registration mode
                    if registration_mode == 'TEAM' and referral.referral_type != 'TEAM':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid referral code for team registration.'
                        }, status=400)
                    
                    # If solo registration, check if alumni referral
                    if registration_mode == 'SOLO' and referral.referral_type != 'ALUMNI':
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid referral code for solo registration.'
                        }, status=400)
                    
                    # Check if referral code is expired
                    if referral.expires_at and referral.expires_at < timezone.now():
                        return JsonResponse({
                            'status': 'error',
                            'message': 'This referral code has expired.'
                        }, status=400)
                        
                except ReferralCode.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid referral code.'
                    }, status=400)
            
            # Create registration with referral code if valid
            registration = FlamesRegistration.objects.create(
                course=course,
                full_name=full_name,
                email=email,
                contact_number=contact_number,
                college=college,
                year=year,
                registration_mode=registration_mode,
                referral_code=referral
            )
            
            # Build response message
            message = f'Successfully registered for {course.title}!'
            if referral:
                message += f' A discount of ₹{referral.discount_amount} has been applied.'
            
            return JsonResponse({
                'status': 'success',
                'message': message
            })
        except FlamesCourse.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Course not found or not active.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

# ============================= VALIDATE REFERRAL CODE ==========================

def validate_referral(request):
    """Validate referral code and return price details"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        code = request.GET.get('code', '')
        print("code")
        course_id = request.GET.get('course_id', '')
        registration_mode = request.GET.get('registration_mode', '')
        
        # Validate input
        if not code or not course_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required parameters.'
            }, status=400)
        
        try:
            # Get the course
            course = FlamesCourse.objects.get(id=course_id, is_active=True)
            
            # Check if referral code exists and is valid
            try:
                referral = ReferralCode.objects.get(code=code, is_active=True)
                
                # Validate referral code type matches registration mode
                if registration_mode == 'TEAM' and referral.referral_type != 'TEAM':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'This code can only be used for solo registrations.'
                    })
                
                # If solo registration, check if alumni referral
                if registration_mode == 'SOLO' and referral.referral_type != 'ALUMNI':
                    return JsonResponse({
                        'status': 'error',
                        'message': 'This code can only be used for team registrations.'
                    })
                
                # Check if referral code is expired
                if referral.expires_at and referral.expires_at < timezone.now():
                    return JsonResponse({
                        'status': 'error',
                        'message': 'This referral code has expired.'
                    })
                
                # Calculate discounted price
                original_price = course.price
                discounted_price = max(0, original_price - referral.discount_amount)
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Valid referral code.',
                    'original_price': original_price,
                    'discounted_price': discounted_price,
                    'discount_amount': referral.discount_amount
                })
                
            except ReferralCode.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid referral code.'
                })
                
        except FlamesCourse.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Course not found or not active.'
            })
            
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method.'
    }, status=400)

# ============================= NEW FLAMES REGISTRATION PAGE ==========================

def register_flames(request, slug):
    """
    Handle Flames course registration through a dedicated page
    """
    try:
        course = get_object_or_404(FlamesCourse, slug=slug, is_active=True)
        
        # Check if the user is already registered for this course
        if request.user.is_authenticated:
            existing_registration = FlamesRegistration.objects.filter(
                course=course,
                email=request.user.email
            ).exists()
            
            if existing_registration:
                messages.info(request, f"You are already registered for {course.title}.")
                # If they're already registered, redirect to student dashboard if authenticated
                return redirect('student_dashboard')
        
        if request.method == 'POST':
            # Get form data
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            contact_number = request.POST.get('contact_number')
            college = request.POST.get('college')
            year = request.POST.get('year')
            registration_mode = request.POST.get('registration_mode')
            referral_code_text = request.POST.get('referral_code')
            
            # Process referral code if provided
            referral = None
            if referral_code_text:
                try:
                    referral = ReferralCode.objects.get(code=referral_code_text, is_active=True)
                    
                    # Validate referral code type matches registration mode
                    if registration_mode == 'TEAM' and referral.referral_type != 'TEAM':
                        messages.error(request, 'Invalid referral code for team registration.')
                        return render(request, "home/flames_register.html", {'course': course, 'user': request.user})
                    
                    # If solo registration, check if alumni referral
                    if registration_mode == 'SOLO' and referral.referral_type != 'ALUMNI':
                        messages.error(request, 'Invalid referral code for solo registration.')
                        return render(request, "home/flames_register.html", {'course': course, 'user': request.user})
                    
                    # Check if referral code is expired
                    if referral.expires_at and referral.expires_at < timezone.now():
                        messages.error(request, 'This referral code has expired.')
                        return render(request, "home/flames_register.html", {'course': course, 'user': request.user})
                        
                except ReferralCode.DoesNotExist:
                    messages.error(request, 'Invalid referral code.')
                    return render(request, "home/flames_register.html", {'course': course, 'user': request.user})
            
            # Create the registration
            registration = FlamesRegistration.objects.create(
                course=course,
                full_name=full_name,
                email=email,
                contact_number=contact_number,
                college=college,
                year=year,
                registration_mode=registration_mode,
                referral_code=referral,
                user=request.user if request.user.is_authenticated else None
            )
            
            # If team registration, process team members
            if registration_mode == 'TEAM':
                # Create a team
                team_name = f"Team {full_name.split()[0]}"
                team = FlamesTeam.objects.create(
                    name=team_name,
                    team_leader=request.user if request.user.is_authenticated else None,
                    course=course
                )
                
                # Associate the team with the registration
                registration.team = team
                registration.save()
                
                # Create team leader as first member
                FlamesTeamMember.objects.create(
                    team=team,
                    full_name=full_name,
                    email=email,
                    contact_number=contact_number,
                    user=request.user if request.user.is_authenticated else None,
                    is_leader=True
                )
                
                # Process additional team members
                for i in range(1, 5):  # Process 4 more members to make a total of 5
                    member_name = request.POST.get(f'team_member_name_{i}')
                    member_email = request.POST.get(f'team_member_email_{i}')
                    member_contact = request.POST.get(f'team_member_contact_{i}')
                    
                    if member_name and member_email and member_contact:
                        FlamesTeamMember.objects.create(
                            team=team,
                            full_name=member_name,
                            email=member_email,
                            contact_number=member_contact
                        )
            
            # Show success message and redirect
            if referral:
                messages.success(request, f"Successfully registered for {course.title}! A discount of ₹{referral.discount_amount} has been applied.")
            else:
                messages.success(request, f"Successfully registered for {course.title}!")
            
            # If the user is logged in, redirect to their dashboard
            if request.user.is_authenticated:
                return redirect('student_dashboard')
            else:
                # If not logged in, suggest creating an account to track progress
                return render(request, "home/registration_success.html", {
                    'course': course,
                    'registration': registration
                })
                
        # GET request - show registration form
        return render(request, "home/flames_register.html", {'course': course, 'user': request.user})
        
    except FlamesCourse.DoesNotExist:
        messages.error(request, "Course not found or not active.")
        return redirect('flames')

# ========================== PORTAL REGISTRATION INTEGRATION ====================


def student_enroll_course(request, course_id):
    """
    Handle direct enrollment for existing portal users or after registration
    This view would be in the student app, but showing the logic here
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next=/student/enroll/{course_id}/")
    
    try:
        course = FlamesCourse.objects.get(id=course_id, is_active=True)
        
        # Check if the user is already registered for this course
        existing_registration = FlamesRegistration.objects.filter(
            course=course,
            email=request.user.email
        ).exists()
        
        if existing_registration:
            messages.info(request, f"You are already registered for {course.title}.")
            return redirect('student_dashboard')
        
        # Create a new registration
        registration = FlamesRegistration.objects.create(
            course=course,
            full_name=f"{request.user.first_name} {request.user.last_name}",
            email=request.user.email,
            contact_number=request.user.profile.contact_number if hasattr(request.user, 'profile') else "",
            college=request.user.profile.college if hasattr(request.user, 'profile') else "",
            year=request.user.profile.year if hasattr(request.user, 'profile') else "",
            registration_mode="SOLO"  # Default to solo for portal registrations
        )
        
        messages.success(request, f"Successfully enrolled in {course.title}!")
        return redirect('student_dashboard')
        
    except FlamesCourse.DoesNotExist:
        messages.error(request, "Course not found or not active.")
        return redirect('student_dashboard')

# ================================= STUDENT FLAMES MANAGEMENT ============================

@login_required
def student_flames(request):
    """
    Display the student's Flames registrations and available courses
    """
    # Get student's registrations
    registrations = FlamesRegistration.objects.filter(
        user=request.user
    ).select_related('course', 'team').order_by('-created_at')
    
    # Prefetch team members for teams the student is part of
    for registration in registrations:
        if registration.team:
            registration.team.members_list = FlamesTeamMember.objects.filter(team=registration.team)
    
    # Get available courses (courses that the student hasn't registered for)
    registered_course_ids = registrations.values_list('course_id', flat=True)
    available_courses = FlamesCourse.objects.filter(is_active=True).exclude(id__in=registered_course_ids)
    
    context = {
        'registrations': registrations,
        'available_courses': available_courses,
        'active_tab': 'flames'
    }
    
    return render(request, 'student/flames.html', context)

@login_required
def student_teams(request):
    """
    Manage team formation for solo registrations
    """
    # Get student's solo registrations that don't have a team yet
    solo_registrations = FlamesRegistration.objects.filter(
        user=request.user,
        registration_mode='SOLO',
        team__isnull=True
    ).select_related('course')
    
    # Get student's teams
    teams = FlamesTeam.objects.filter(
        team_leader=request.user
    ).prefetch_related('members')
    
    context = {
        'solo_registrations': solo_registrations,
        'teams': teams,
        'active_tab': 'flames_teams'
    }
    
    return render(request, 'student/team_formation.html', context)

@login_required
def student_create_team(request, registration_id):
    """
    Create a team for a solo registration
    """
    registration = get_object_or_404(
        FlamesRegistration, 
        id=registration_id, 
        user=request.user, 
        registration_mode='SOLO',
        team__isnull=True
    )
    
    if request.method == 'POST':
        team_name = request.POST.get('team_name')
        
        if not team_name:
            messages.error(request, "Team name is required.")
            return redirect('student_teams')
        
        # Create the team
        team = FlamesTeam.objects.create(
            name=team_name,
            team_leader=request.user,
            course=registration.course
        )
        
        # Link the registration to the team
        registration.team = team
        registration.save()
        
        # Add the user as the first team member
        FlamesTeamMember.objects.create(
            team=team,
            full_name=registration.full_name,
            email=registration.email,
            contact_number=registration.contact_number,
            user=request.user,
            is_leader=True
        )
        
        messages.success(request, f"Team '{team_name}' created successfully!")
        return redirect('student_teams')
    
    # GET request
    return render(request, 'student/create_team.html', {
        'registration': registration,
        'active_tab': 'flames_teams'
    })

@login_required
def student_add_team_member(request, team_id):
    """
    Add a team member to an existing team
    """
    team = get_object_or_404(FlamesTeam, id=team_id, team_leader=request.user)
    
    # Check if team is already full
    if team.members.count() >= 5:
        messages.error(request, "This team already has the maximum number of members (5).")
        return redirect('student_teams')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        contact_number = request.POST.get('contact_number')
        
        if not all([full_name, email, contact_number]):
            messages.error(request, "All fields are required.")
            return redirect('student_add_team_member', team_id=team.id)
        
        # Check if email is already in the team
        if team.members.filter(email=email).exists():
            messages.error(request, f"A member with email '{email}' is already in this team.")
            return redirect('student_add_team_member', team_id=team.id)
        
        # Add new team member
        FlamesTeamMember.objects.create(
            team=team,
            full_name=full_name,
            email=email,
            contact_number=contact_number
        )
        
        messages.success(request, f"{full_name} has been added to the team.")
        return redirect('student_teams')
    
    # GET request
    return render(request, 'student/add_team_member.html', {
        'team': team,
        'active_tab': 'flames_teams'
    })

@login_required
def student_remove_team_member(request, member_id):
    """
    Remove a team member from a team
    """
    # Only allow removal if the user is the team leader and the member is not the leader
    member = get_object_or_404(
        FlamesTeamMember, 
        id=member_id, 
        team__team_leader=request.user,
        is_leader=False
    )
    
    team = member.team
    member_name = member.full_name
    
    # Delete the member
    member.delete()
    
    messages.success(request, f"{member_name} has been removed from the team.")
    return redirect('student_teams')
