from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
print("DEBUG: accounts.adapters module loaded")
from allauth.core.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ValidationError
import logging

from django.contrib.auth.models import User
from .models import Student, Instructor, Administrator
from .views import send_welcome_mail, send_verification_mail

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for additional account management control.
    """
    
    def respond_user_inactive(self, request, user):
        print(f"DEBUG: respond_user_inactive called for {user.email}")
        """
        Redirect inactive users to the verification sent page instead of login.
        Also resend the verification email to ensure they have the link.
        """
        from .views import send_verification_mail
        from django.shortcuts import render
        
        try:
            # Trigger resend of verification mail
            send_verification_mail(user, request)
            logger.info(f"Resent verification email to inactive user: {user.email}")
        except Exception as e:
            logger.error(f"Failed to resend verification email: {e}")
            
        return render(request, "accounts/verification_sent.html", {"email": user.email})

    
    def add_message(self, request, level, message_template, message_context=None, extra_tags=''):
        """
        Override to suppress specific messages like "Successfully signed in as...".
        """
        # Suppress the "Successfully signed in as..." message
        if message_template == 'account/messages/logged_in.txt':
            return
            
        super().add_message(request, level, message_template, message_context, extra_tags)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for Google OAuth handling.
    """
    
    def is_open_for_signup(self, request, sociallogin):
        email = sociallogin.account.extra_data.get('email')
        print(f"DEBUG: is_open_for_signup called for {email}")
        """
        Control whether social signup is allowed.
        Only allow Google provider with verified email.
        """
        # Only allow Google provider
        if sociallogin.account.provider != 'google':
            print("DEBUG: is_open_for_signup: not google")
            return False
        
        # Check if email is verified
        email_verified = sociallogin.account.extra_data.get('email_verified')
        print(f"DEBUG: is_open_for_signup: email_verified={email_verified}")
        
        # Temporary loosen for debugging
        return True
    
    def pre_social_login(self, request, sociallogin):
        print(f"DEBUG: pre_social_login called for {sociallogin.account.extra_data.get('email')}")
        """
        Invoked just after a user successfully authenticates via a social provider,
        but before the login is actually processed.
        """
        try:
            # Get user data from social account
            user_data = sociallogin.account.extra_data
            email = user_data.get('email', '').lower()
            provider = sociallogin.account.provider
            
            # Security check: Only allow Google
            if provider != 'google':
                messages.error(request, "Only Google login is supported for students.")
                raise ImmediateHttpResponse(redirect('login'))
            
            # Check email verification
            if not user_data.get('email_verified', False):
                messages.error(request, "Please verify your email with Google before logging in.")
                raise ImmediateHttpResponse(redirect('login'))
            
            # Check if email belongs to staff (Instructor/Administrator)
            if (Instructor.objects.filter(email=email).exists() or 
                Administrator.objects.filter(email=email).exists()):
                messages.error(request, "This email is registered as staff. Please use username/password login.")
                raise ImmediateHttpResponse(redirect('login'))
            
            # Check if user exists as Student with this email
            if Student.objects.filter(email=email).exists():
                existing_student = Student.objects.get(email=email)
                
                # Set the sociallogin user to the existing student
                # This tells allauth to use this existing user instead of creating a new one
                sociallogin.user = existing_student
                
                logger.info(f"Existing student logging in via Google: {email}")
                
            # Check for "Zombie" users - User exists but not Student (failed previous signup)
            elif User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                
                # Heal the split user by converting to Student
                logger.info(f"Repairing user account for Google login: {email}")
                
                # Create Student instance pointing to existing User
                student = Student(user_ptr=user)
                student.__dict__.update(user.__dict__)
                
                # Set default student fields
                student.mobile_number = '-'
                student.gender = 'Not Set'
                student.college = None
                student.dob = None
                student.is_changed_password = False
                student.profile_pic = '/student_profile/default.jpg'
                student.linkedin_id = None
                student.github_id = None
                student.coins = 100
                
                student.save()
                
                sociallogin.user = student
                logger.info(f"Repaired and logged in student: {email}")

            else:
                # New user - allow to proceed to signup
                logger.info(f"New student signup via Google: {email}")
            
        except ImmediateHttpResponse:
            raise
        except Exception as e:
            logger.error(f"Error in pre_social_login: {e}", exc_info=True)
            messages.error(request, "An error occurred during login. Please try again.")
            raise ImmediateHttpResponse(redirect('login'))
    
    def save_user(self, request, sociallogin, form=None):
        print(f"DEBUG: save_user called for {sociallogin.account.extra_data.get('email')}")
        """
        Save user from social login. Creates Student profile directly to avoid signal race conditions.
        """
        try:
            # Get social account data
            user_data = sociallogin.account.extra_data
            
            # Validate email exists
            email = user_data.get('email', '').lower().strip()
            if not email:
                raise ValidationError("Email is required for Google OAuth registration.")
            
            # Create a new Student instance explicitly
            # We don't use sociallogin.user (which is a User instance) directly
            # We create a Student instance and populate it
            
            user = Student()
            
            # Generate unique username if not already set
            username = self.generate_unique_username(user_data)
            user.username = username
            
            # Update user fields from Google data with fallbacks
            user.first_name = user_data.get('given_name', '').strip() or 'Not Set'
            user.last_name = user_data.get('family_name', '').strip() or ''
            user.email = email
            
            # Ensure user is inactive initially
            user.is_active = False # Changed to False for verification
            user.is_staff = False
            user.is_superuser = False
            
            # Student specific fields
            user.mobile_number = '-'
            user.gender = 'Not Set'
            user.college = None
            user.dob = None
            user.is_changed_password = False
            user.profile_pic = '/student_profile/default.jpg'
            user.linkedin_id = None
            user.github_id = None
            user.coins = 100
            
            # Save the user (this saves both User and Student tables)
            user.save()
            
            # Important: Update sociallogin.user to point to our new Student instance
            sociallogin.user = user
            
            # Send verification email
            try:
                if user.email and user.email != 'Not Set':
                    send_verification_mail(user, request)
            except Exception as email_error:
                logger.error(f"Failed to send verification email inside save_user: {email_error}", exc_info=True)
            
            logger.info(f"Student created directly from Google OAuth: {user.username} ({user.email})")
            
            return user
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error in save_user: {e}", exc_info=True)
            raise ValidationError(f"Failed to create user account: {str(e)}")
    
    def generate_unique_username(self, user_data):
        """
        Generate a unique username from Google user data.
        """
        import re
        
        # Get base username from Google data
        first_name = user_data.get('given_name', '') or 'user'
        base_username = first_name.lower().strip()
        
        # Clean username - remove special characters and spaces
        base_username = re.sub(r'[^a-zA-Z0-9]', '', base_username)
        if not base_username:
            base_username = 'user'
        
        # Find unique username
        username = base_username
        counter = 1
        while (Student.objects.filter(username=username).exists() or 
               Instructor.objects.filter(username=username).exists() or 
               Administrator.objects.filter(username=username).exists()):
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    def get_login_redirect_url(self, request):
        """
        Custom redirect after successful social login.
        Redirect to student dashboard.
        """
        try:
            url = reverse('student')
            logger.info(f"Redirecting to student dashboard: {url}")
            return url
        except Exception as e:
            logger.error(f"Error getting login redirect URL: {e}")
            return '/dashboard/'
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        Handle authentication errors gracefully.
        """
        logger.error(f"Social authentication error for {provider_id}: {error}", exc_info=True)
        
        error_messages = {
            'cancelled': "Google login was cancelled.",
            'denied': "Access was denied. Please grant necessary permissions.",
            'invalid_request': "Invalid request during authentication.",
            'server_error': "Server error occurred during authentication.",
        }
        
        message = error_messages.get(error, "An error occurred during Google login.")
        messages.error(request, message)
        
        return redirect('login')
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Control automatic signup behavior.
        """
        # Allow auto signup for Google accounts with verified email
        if sociallogin.account.provider == 'google':
            return sociallogin.account.extra_data.get('email_verified', False)
        
        return False
    

    
    def get_connect_redirect_url(self, request, socialaccount):
        """
        Redirect URL after connecting a social account.
        """
        return reverse('student')
