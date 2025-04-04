from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import FlamesCourse, FlamesCourseTestimonial, FlamesRegistration, ReferralCode, FlamesTeam, FlamesTeamMember
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db import transaction
from accounts.models import Student

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
    Handle Flames course registration through a dedicated page with automatic
    student account creation and login
    """
    
    course = get_object_or_404(FlamesCourse, slug=slug, is_active=True)
    
    # If user is logged in, check if they're already registered
    if request.user.is_authenticated and hasattr(request.user, 'student'):
        existing_registration = FlamesRegistration.objects.filter(
            user=request.user.student,
            course=course
        ).first()
        
        if existing_registration:
            messages.warning(request, f"You have already registered for {course.title}.")
            return redirect('student_flames')
    
    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name')
        email = request.POST.get('email').lower()  # Normalize email to lowercase
        contact_number = request.POST.get('contact_number')
        college = request.POST.get('college', '')
        year = request.POST.get('year')
        message = request.POST.get('message', '')
        registration_mode = request.POST.get('registration_mode', 'SOLO')
        referral_code_text = request.POST.get('referral_code', '')
        
        # Get first and last name from full name
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Get referral code if provided
        referral_code = None
        if referral_code_text:
            try:
                referral_code = ReferralCode.objects.get(code=referral_code_text, is_active=True)
                
                # Validate referral code type matches registration mode
                if registration_mode == 'TEAM' and referral_code.referral_type != 'TEAM':
                    messages.error(request, 'Invalid referral code for team registration.')
                    return render(request, "home/flames_register.html", {'course': course, 'user': request.user})
                
                # If solo registration, check if alumni referral
                if registration_mode == 'SOLO' and referral_code.referral_type != 'ALUMNI':
                    messages.error(request, 'Invalid referral code for solo registration.')
                    return render(request, "home/flames_register.html", {'course': course, 'user': request.user})
                
                # Check if referral code is expired
                if referral_code.expires_at and referral_code.expires_at < timezone.now():
                    messages.error(request, 'This referral code has expired.')
                    return render(request, "home/flames_register.html", {'course': course, 'user': request.user})
                    
            except ReferralCode.DoesNotExist:
                messages.error(request, 'Invalid referral code.')
                return render(request, "home/flames_register.html", {'course': course, 'user': request.user})
        
        with transaction.atomic():
            # Check if user already exists
            student = None
            user_exists = Student.objects.filter(email=email).exists()
            
            if request.user.is_authenticated and hasattr(request.user, 'student'):
                # Use the logged-in student
                student = request.user.student
            elif user_exists:
                # User exists but not logged in - we'll handle login later
                student = Student.objects.get(email=email)
            else:
                # Create a new student account
                # Get username and password from form if provided
                username = request.POST.get('username')
                password = request.POST.get('password')
                
                # If username not provided, generate from email
                if not username:
                    username = email.split('@')[0]
                    base_username = username
                    counter = 1
                    
                    # Ensure username is unique
                    while Student.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                
                # Create the student with the provided or temporary password
                student = Student.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    mobile_number=contact_number,
                    college=college,
                    is_active=True
                )
                
                # Set password
                if password:
                    student.set_password(password)
                else:
                    # Set a temporary password if not provided
                    temp_password = Student.objects.make_random_password()
                    student.set_password(temp_password)
                    # TODO: Send welcome email with temporary password
                
                student.save()
            
            # Create the registration
            registration = FlamesRegistration(
                user=student,
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
                if not team_name:
                    team_name = f"Team {first_name}"
                
                # Create the team
                team = FlamesTeam.objects.create(
                    name=team_name,
                    team_leader=student,
                    course=course
                )
                
                # Link the registration to the team
                registration.team = team
                registration.save()
                
                # Add the user as the first team member (team leader)
                FlamesTeamMember.objects.create(
                    team=team,
                    full_name=full_name,
                    email=email,
                    contact_number=contact_number,
                    user=student,
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
                
                messages.success(request, f"Team '{team_name}' has been registered for {course.title} successfully!")
            else:
                # Solo registration
                messages.success(request, f"You have been registered for {course.title} successfully!")
            
            # Log the user in if they're not already logged in
            if not request.user.is_authenticated:
                login(request, student)
                messages.info(request, "You have been automatically logged into your student account.")
            
            # Redirect to the summer training page
            return redirect('student_flames')
    
    # GET request - show registration form
    return render(request, "home/flames_register.html", {
        'course': course,
        'user': request.user if request.user.is_authenticated else None
    })


# ========================== INTEGRATED REGISTRATION FLOW ====================

# from django.contrib.auth import login
# from django.db import transaction
# from accounts.models import Student

# def integrated_flames_register(request, slug):
#     """
#     Integrated registration flow that:
#     1. Registers a user for a FLAMES course
#     2. Creates a Student account if the user doesn't have one
#     3. Automatically logs the user in
#     4. Redirects to the summer training page
#     """
#     course = get_object_or_404(FlamesCourse, slug=slug, is_active=True)
    
#     # If user is already logged in, check if they're already registered
#     if request.user.is_authenticated and hasattr(request.user, 'student'):
#         existing_registration = FlamesRegistration.objects.filter(
#             user=request.user.student,
#             course=course
#         ).first()
        
#         if existing_registration:
#             messages.warning(request, f"You have already registered for {course.title}.")
#             return redirect('student_flames')
    
#     if request.method == 'POST':
#         # Get form data
#         registration_mode = request.POST.get('registration_mode')
#         full_name = request.POST.get('full_name')
#         email = request.POST.get('email').lower()  # Normalize email to lowercase
#         contact_number = request.POST.get('contact_number')
#         college = request.POST.get('college', '')
#         year = request.POST.get('year')
#         message = request.POST.get('message', '')
#         referral_code_text = request.POST.get('referral_code', '')
        
#         # Get first and last name from full name
#         name_parts = full_name.split(' ', 1)
#         first_name = name_parts[0]
#         last_name = name_parts[1] if len(name_parts) > 1 else ''
        
#         # Get referral code if provided
#         referral_code = None
#         if referral_code_text:
#             referral_code = ReferralCode.objects.filter(code=referral_code_text, is_active=True).first()
        
#         with transaction.atomic():
#             # Check if user already exists
#             student = None
#             user_exists = Student.objects.filter(email=email).exists()
            
#             if request.user.is_authenticated and hasattr(request.user, 'student'):
#                 # Use the logged-in student
#                 student = request.user.student
#             elif user_exists:
#                 # User exists but not logged in - we'll handle login later
#                 student = Student.objects.get(email=email)
#             else:
#                 # Create a new student account
#                 # Generate username from email (first part before @)
#                 username = email.split('@')[0]
#                 base_username = username
#                 counter = 1
                
#                 # Ensure username is unique
#                 while Student.objects.filter(username=username).exists():
#                     username = f"{base_username}{counter}"
#                     counter += 1
                
#                 # Create the student with a temporary password
#                 student = Student.objects.create(
#                     username=username,
#                     email=email,
#                     first_name=first_name,
#                     last_name=last_name,
#                     mobile_number=contact_number,
#                     college=college,
#                     is_active=True
#                 )
                
#                 # Set a temporary password (they can reset it later)
#                 temp_password = Student.objects.make_random_password()
#                 student.set_password(temp_password)
#                 student.save()
                
#                 # TODO: Send welcome email with temporary password
            
#             # Create the registration
#             registration = FlamesRegistration(
#                 user=student,
#                 course=course,
#                 year=year,
#                 message=message,
#                 registration_mode=registration_mode,
#                 referral_code=referral_code
#             )
            
#             # Save registration to calculate prices
#             registration.save()
            
#             # Handle team registration
#             if registration_mode == 'TEAM':
#                 team_name = request.POST.get('team_name')
#                 team_member_count = int(request.POST.get('team_member_count', 1))
                
#                 # Create the team
#                 team = FlamesTeam.objects.create(
#                     name=team_name,
#                     team_leader=student,
#                     course=course
#                 )
                
#                 # Link the registration to the team
#                 registration.team = team
#                 registration.save()
                
#                 # Add the user as the first team member (team leader)
#                 FlamesTeamMember.objects.create(
#                     team=team,
#                     full_name=full_name,
#                     email=email,
#                     contact_number=contact_number,
#                     user=student,
#                     is_leader=True
#                 )
                
#                 # Add additional team members
#                 for i in range(2, team_member_count + 1):
#                     member_name = request.POST.get(f'member_name_{i}')
#                     member_email = request.POST.get(f'member_email_{i}')
#                     member_contact = request.POST.get(f'member_contact_{i}')
                    
#                     if member_name and member_email and member_contact:
#                         FlamesTeamMember.objects.create(
#                             team=team,
#                             full_name=member_name,
#                             email=member_email,
#                             contact_number=member_contact
#                         )
                
#                 messages.success(request, f"Team '{team_name}' has been registered for {course.title} successfully!")
#             else:
#                 # Solo registration
#                 messages.success(request, f"You have been registered for {course.title} successfully!")
            
#             # Log the user in if they're not already logged in
#             if not request.user.is_authenticated:
#                 login(request, student)
#                 messages.info(request, "You have been automatically logged into your student account.")
            
#             # Redirect to the summer training page
#             return redirect('student_flames')
    
#     context = {
#         'course': course,
#         'user': request.user if request.user.is_authenticated else None,
#     }
    
#     return render(request, 'home/integrated_flames_register.html', context)

