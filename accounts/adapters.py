from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ValidationError
import logging

from .models import Student, Instructor, Administrator

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for additional account management control.
    """
    
    def is_open_for_signup(self, request):
        """
        Allow signup only through social accounts for students.
        Regular signup is handled separately.
        """
        return True
    
    def save_user(self, request, user, form, commit=True):
        """
        Save user with additional validation.
        """
        user = super().save_user(request, user, form, commit=False)
        
        # Additional validation can be added here
        if commit:
            user.save()
        
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for Google OAuth handling.
    """
    
    def is_open_for_signup(self, request, sociallogin):
        """
        Control whether social signup is allowed.
        """
        # Only allow Google provider
        if sociallogin.account.provider != 'google':
            return False
        
        # Check if email is verified
        email_verified = sociallogin.account.extra_data.get('email_verified', False)
        if not email_verified:
            return False
        
        return True
    
    def pre_social_login(self, request, sociallogin):
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
            
            # If user exists as Student, connect the account
            try:
                existing_student = Student.objects.get(email=email)
                if sociallogin.user.pk != existing_student.pk:
                    # Connect social account to existing student
                    sociallogin.connect(request, existing_student)
                    messages.success(request, f"Welcome back, {existing_student.first_name}!")
                    raise ImmediateHttpResponse(redirect('student'))
            except Student.DoesNotExist:
                pass
            
        except ImmediateHttpResponse:
            raise
        except Exception as e:
            logger.error(f"Error in pre_social_login: {e}", exc_info=True)
            messages.error(request, "An error occurred during login. Please try again.")
            raise ImmediateHttpResponse(redirect('login'))
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user from social login with custom Student profile creation.
        """
        try:
            # Get the user from sociallogin
            user = sociallogin.user
            
            # Get social account data
            user_data = sociallogin.account.extra_data
            
            # Generate unique username
            username = self.generate_unique_username(user_data)
            
            # Update user fields
            user.username = username
            user.first_name = user_data.get('given_name', '') or user.first_name or 'Not Set'
            user.last_name = user_data.get('family_name', '') or user.last_name or 'Not Set'
            user.email = user_data.get('email', '') or user.email or 'Not Set'
            
            # Save the user first
            user.save()
            
            # Create Student profile
            student = Student.objects.create(
                user_ptr=user,
                username=username,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                mobile_number='-',
                gender='Not Set',
            )
            
            logger.info(f"Created new student via Google OAuth: {student.username}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error in save_user: {e}", exc_info=True)
            raise ValidationError("Failed to create user account. Please try again.")
    
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
        """
        # Always redirect students to dashboard
        return reverse('student')
    
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
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user fields from social account data.
        """
        user = sociallogin.user
        user_data = sociallogin.account.extra_data
        
        # Set user fields from Google data
        user.first_name = user_data.get('given_name', '') or data.get('first_name', '')
        user.last_name = user_data.get('family_name', '') or data.get('last_name', '')
        user.email = user_data.get('email', '') or data.get('email', '')
        
        # Ensure email is set
        if not user.email:
            raise ValidationError("Email is required for account creation.")
        
        return user
    
    def get_connect_redirect_url(self, request, socialaccount):
        """
        Redirect URL after connecting a social account.
        """
        messages.success(request, "Google account successfully connected!")
        return reverse('student')
