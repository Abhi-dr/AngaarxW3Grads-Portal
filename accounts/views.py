from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

from django.db import transaction
from django.db.models import Q
from django.contrib.auth import login as default_login

from .models import Student, Instructor, Administrator, PasswordResetToken

from django.utils.timezone import now
from practice.models import Sheet

from django_ratelimit.decorators import ratelimit

# ===================================== LOGIN ==============================

@ratelimit(key='post:username', rate='3/m', method=['POST'], block=False)
def login(request):
    if request.user.is_authenticated:
        # Redirect based on user type
        if hasattr(request.user, 'student'):
            return redirect('student')
        elif hasattr(request.user, 'instructor'):
            return redirect('instructor')
        elif hasattr(request.user, 'administrator'):
            return redirect('administration')
        else:
            return redirect('home')  # Default fallback

    if getattr(request, 'limited', False):
        messages.error(request, "Too many login attempts for this Username. Please try again after 1 minute.")
        return redirect('login')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        username = request.POST.get('username').strip().lower()
        password = request.POST.get('password')

        if Student.objects.filter(username=username).exists():
            user = auth.authenticate(username=username, password=password)

            if user is not None:
                auth.login(request, user)
                return redirect(next_url if next_url else 'student')

            messages.error(request, "Invalid Password")
            return redirect("login")

        elif Instructor.objects.filter(username=username).exists():
            user = auth.authenticate(username=username, password=password)

            if user is not None:
                auth.login(request, user)
                return redirect(next_url if next_url else 'instructor')

            messages.error(request, "Invalid Password")
            return redirect("login")

        elif Administrator.objects.filter(username=username).exists():
            user = auth.authenticate(username=username, password=password)

            if user is not None:
                auth.login(request, user)
                return redirect(next_url if next_url else 'administration')

            messages.error(request, "Invalid Password")
            return redirect("login")

        else:
            messages.error(request, "Invalid Username or Password")
            return redirect("login")

    return render(request, 'accounts/login.html', {'next': next_url})

# ===================================== REGISTER ==============================

def register(request):
    if request.user.is_authenticated:
        # Redirect logged-in users to the dashboard
        if hasattr(request.user, 'student'):
            return redirect('student')
        elif hasattr(request.user, 'instructor'):
            return redirect('instructor')
        elif hasattr(request.user, 'administrator'):
            return redirect('administration')
        else:
            return redirect('home')  # Default fallback

    next_url = request.GET.get('next', '')

    if request.method == "POST":
        username = request.POST.get("username").strip().lower()
        first_name = request.POST.get("first_name").strip().title()
        last_name = request.POST.get("last_name").strip().title()
        email = request.POST.get("email").strip().lower()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        # Optimized Query for checking existing username or email
        if Student.objects.filter(Q(username=username) | Q(email=email)).exists():
            messages.error(request, "Username or Email already exists!")
            return redirect("register")

        try:
            with transaction.atomic():  # Ensures rollback in case of failure
                new_user = Student.objects.create(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                )
                new_user.set_password(password)
                new_user.save()

                send_welcome_mail(email, first_name)

                messages.success(request, "Account created successfully! Aaja Ab🔥")

                # Auto-login user after registration (optional)
                default_login(request, new_user)

                return redirect(next_url if next_url else "student")

        except Exception as e:
            messages.error(request, f"Something went wrong: {e}")
            return redirect("register")

    return render(request, "accounts/register.html", {"next": next_url})


# =================================== logout ============================

@login_required(login_url="login")
def logout(request):
     auth.logout(request)
     return redirect("home")

# ====================== check username availability ====================

def check_username_availability(request):
    username = request.GET.get('username', '')
    data = {'is_available': 
        not (Student.objects.filter(username=username).exists() 
        or Instructor.objects.filter(username=username).exists() 
        or Administrator.objects.filter(username=username).exists())}
    
    print(data)

    return JsonResponse(data)

def check_username_exists(request):
    """Check if a username exists in the Student model and return user details"""
    username = request.GET.get('username')
    course_id = request.GET.get('course_id')
    
    student = Student.objects.filter(username=username).first()
    exists = student is not None
    
    response_data = {'exists': exists}
    
    if exists:        
        if student:
            # Add student details to response
            response_data['full_name'] = f"{student.first_name} {student.last_name}"
            response_data['email'] = student.email
            
            # Check if student is already registered for this course
            if course_id:
                from home.models import FlamesRegistration
                already_registered = FlamesRegistration.objects.filter(
                    user=student,
                    course_id=course_id
                ).exists()
                response_data['already_registered'] = already_registered
    
    return JsonResponse(response_data)

# ====================== check email availability ====================
def check_email_availability(request):
    email = request.GET.get('email', '')
    data = {'is_available': 
        not (Student.objects.filter(email=email).exists() 
        or Instructor.objects.filter(email=email).exists() 
        or Administrator.objects.filter(email=email).exists())}
    
    return JsonResponse(data)

# ====================== block student ====================

@login_required(login_url="login")
@staff_member_required(login_url="login")
def block_student(request, id):
    student = Student.objects.get(id=id)
    student.is_active = not student.is_active
    student.save()
    
    messages.success(request, f"{student.username} is blocked successfully!")

    return redirect('all_students')

# ====================== unblock student ====================

@login_required(login_url="login")
@staff_member_required(login_url="login")
def unblock_student(request, id):
    student = Student.objects.get(id=id)
    student.is_active = not student.is_active
    student.save()
    
    messages.success(request, f"{student.username} is unblocked successfully!")

    return redirect('all_students')


# ============================ 404 ===============

def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)


# =========================================================

@login_required
def get_active_sheet_timer(request):
    # Find the active sheet for the logged-in user for the batch in which the user has enrolled
    
    active_sheets = Sheet.objects.filter(
        end_time__gte=now()
    )
    
    if active_sheets.exists():
        active_sheet = active_sheets.first()  # Get the first active sheet
        return JsonResponse({
            'start_time': active_sheet.start_time.isoformat(),
            'end_time': active_sheet.end_time.isoformat(),
            'sheetName': active_sheet.name,
            'sheetSlug': active_sheet.slug
        })
    else:
        return JsonResponse({'start_time': None, 'end_time': None})

# ========================================

from django.core.mail import EmailMultiAlternatives


def send_welcome_mail(to, name):

    subject = 'Welcome to The Angaar Batch!🔥'
    from_email = 'noreply@theangaarbatch.in'
    to_email = [to]
    
    from_name = "The Angaar Batch "
    from_email_full = f"{from_name} <{from_email}>"

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 0;">
        <div style="background-color: #f4f4f4; padding: 20px; text-align: center;">
        <img src="https://theangaarbatch.in/static/img/home/angaari_logo.png" alt="The Angaar Batch Logo" style="width: 120px; margin-bottom: 20px;">
        <h1 style="color: #2C3E50;">Welcome to The Angaar Batch🔥, {name}!</h1>
        <p style="font-size: 16px; color: #555555;">We're thrilled to have you on board. Get ready to dive into an exciting journey of learning, coding, and growth.</p>
        <p style="font-size: 16px; color: #555555;">Stay curious, stay passionate, and let's build something amazing together!</p>
        <a href="https://theangaarbatch.in/accounts/login" style="background-color: #3498DB; color: #ffffff; text-decoration: none; padding: 10px 20px; border-radius: 5px; font-size: 14px; display: inline-block; margin-top: 20px;">Go to Dashboard</a>
        <p style="font-size: 14px; color: #777777; margin-top: 30px;">If you have any questions, feel free to reply to this email.</p>
        <p style="font-size: 14px; color: #777777;">Happy Coding! 🚀</p>
        </div>
    </body>
    </html>
    """

    email = EmailMultiAlternatives(subject, '', from_email_full, to_email)
    email.attach_alternative(html_content, 'text/html')
    email.send()
    
    print(f"\nEMAIL SENT! to {to_email} \n")

# ================================================== RESET PASSWORD ==========================================

def request_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = Student.objects.get(email=email)
            
            # check if the user already has a valid token
            if PasswordResetToken.objects.filter(user=user).exists():
                token = PasswordResetToken.objects.get(user=user)
                if token.expires_at > timezone.now():
                    messages.error(request, 'A password reset link has already been sent to your email address!')
                    return redirect('request_password_reset')
            
            token = PasswordResetToken.create_token(user)
            from_email = 'noreply@theangaarbatch.in'
            subject = 'Reset Your Password'

            from_name = "The Angaar Batch "
            from_email_full = f"{from_name} <{from_email}>"
            
            
            reset_link = request.build_absolute_uri(
                f"/accounts/reset-password/{user.pk}/{token}/"
            )

            
            html_message = render_to_string('accounts/reset_password_email.html', {
            'user': user,
            'reset_link': reset_link,
            'current_year': timezone.now().year
        })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject, 
                plain_message, 
                from_email_full, 
                [email], 
                html_message=html_message
            )

            messages.success(request, 'Password reset link sent to your email address!')
            return redirect('login')
        except Student.DoesNotExist:
            messages.error(request, 'No user found with that email address!')
            return redirect('request_password_reset')
            
    return render(request, 'accounts/request_password_reset.html')


def reset_password(request, user_id, token):
    try:
        user = Student.objects.get(pk=user_id)
        reset_token = PasswordResetToken.objects.filter(user=user).first()
    except Student.DoesNotExist:
        reset_token = None

    if reset_token and reset_token.is_valid(token):
        if request.method == 'POST':
            new_password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                reset_token.invalidate()
                return redirect('login')
        return render(request, 'accounts/reset_password.html')
    
    elif reset_token and not reset_token.is_valid(token):
        messages.error(request, 'Invalid or expired reset link!')
        return redirect('request_password_reset')

    return redirect('request_password_reset')

@staff_member_required
def get_students_api(request):
    """API endpoint to get list of students for administrator use."""
    try:
        students = Student.objects.filter(is_active=True).values('id', "first_name", "last_name", 'username', 'email')
        # sort by first_name
        students = students.order_by('first_name')
        return JsonResponse({
            'status': 'success',
            'students': list(students)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
