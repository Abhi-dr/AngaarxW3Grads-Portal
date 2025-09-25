from django.dispatch import receiver
from django.contrib.auth import login
from django.shortcuts import redirect
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
import re

from allauth.socialaccount.signals import pre_social_login, social_account_added
from allauth.socialaccount.models import SocialAccount
from allauth.account.signals import user_signed_up

from .models import Student, Instructor, Administrator
from .views import send_welcome_mail


@receiver(pre_social_login)
def pre_social_login_handler(sender, request, sociallogin, **kwargs):
    """
    Handle pre-social login to check for existing accounts and security measures.
    This signal is fired before the user is logged in via social account.
    """
    try:
        # Get the social account data
        social_account = sociallogin.account
        user_data = social_account.extra_data
        email = user_data.get('email', '')
        
        # Security Check: Only allow Google provider
        if social_account.provider != 'google':
            messages.error(request, "Only Google login is supported for students.")
            return redirect('login')
        
        # Check if email is verified with Google
        if not user_data.get('email_verified', False):
            messages.error(request, "Please verify your email with Google before logging in.")
            return redirect('login')
        
        # Check if user already exists as Instructor or Administrator
        if (Instructor.objects.filter(email=email).exists() or 
            Administrator.objects.filter(email=email).exists()):
            messages.error(request, "This email is registered as staff. Please use username/password login.")
            return redirect('login')
        
        # If user already exists as Student, connect the social account
        try:
            existing_student = Student.objects.get(email=email)
            if not sociallogin.user.pk:
                sociallogin.connect(request, existing_student)
            return
        except Student.DoesNotExist:
            pass
            
    except Exception as e:
        print(f"Error in pre_social_login_handler: {e}")
        messages.error(request, "An error occurred during login. Please try again.")


@receiver(social_account_added)
def social_account_added_handler(sender, request, sociallogin, **kwargs):
    """
    Handle when a social account is added to an existing user.
    """
    try:
        user = sociallogin.user
        social_account = sociallogin.account
        
        if social_account.provider == 'google':
            messages.success(request, f"Google account successfully linked to your profile!")
            
    except Exception as e:
        print(f"Error in social_account_added_handler: {e}")


@receiver(user_signed_up)
def user_signed_up_handler(sender, request, user, sociallogin=None, **kwargs):
    """
    Handle user signup via social login.
    This creates a Student profile for users who sign up via Google.
    """
    if not sociallogin:
        # This is a regular signup, not social login
        return
        
    try:
        with transaction.atomic():
            # Get social account data
            social_account = sociallogin.account
            user_data = social_account.extra_data
            
            if social_account.provider == 'google':
                # Generate unique username from Google data
                first_name = user_data.get('given_name', '') or user.first_name or 'user'
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
                
                # Create Student profile
                student = Student.objects.create(
                    user_ptr=user,
                    username=username,
                    first_name=user_data.get('given_name', '') or user.first_name or 'Not Set',
                    last_name=user_data.get('family_name', '') or user.last_name or 'Not Set',
                    email=user_data.get('email', '') or user.email or 'Not Set',
                    mobile_number='-',
                    gender='Not Set',
                )
                
                # Update the user object with the username
                user.username = username
                user.save()
                
                # Send welcome email
                try:
                    if student.email and student.email != 'Not Set':
                        send_welcome_mail(student.email, student.first_name)
                except Exception as email_error:
                    print(f"Failed to send welcome email: {email_error}")
                
                # Success message
                messages.success(request, f"Welcome to Angaar, {student.first_name}! Your account is ready.")
                
    except Exception as e:
        print(f"Error in user_signed_up_handler: {e}")
        messages.error(request, "An error occurred during account creation. Please try again.")


def validate_google_oauth_settings():
    """
    Validate that Google OAuth is properly configured.
    """
    from django.conf import settings
    
    required_settings = [
        'SOCIALACCOUNT_PROVIDERS',
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not hasattr(settings, setting):
            missing_settings.append(setting)
    
    if missing_settings:
        raise ValidationError(f"Missing required settings for Google OAuth: {missing_settings}")
    
    # Check Google provider configuration
    google_config = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
    if not google_config:
        raise ValidationError("Google provider not configured in SOCIALACCOUNT_PROVIDERS")
    
    return True
