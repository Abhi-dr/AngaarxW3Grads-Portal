from django.dispatch import receiver
from django.contrib.auth import login
from django.contrib.auth.signals import user_logged_in
from django.shortcuts import redirect
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError
import re
import logging

from allauth.socialaccount.signals import pre_social_login, social_account_added
from allauth.socialaccount.models import SocialAccount
from allauth.account.signals import user_signed_up

from .models import Student, Instructor, Administrator
from .views import send_welcome_mail

logger = logging.getLogger(__name__)


@receiver(pre_social_login)
def pre_social_login_handler(sender, request, sociallogin, **kwargs):
    """
    Handle pre-social login to check for existing accounts and security measures.
    This signal is fired before the user is logged in via social account.
    NOTE: Adapter handles the main logic, this is just for logging.
    """
    try:
        # Get the social account data
        social_account = sociallogin.account
        user_data = social_account.extra_data
        email = user_data.get('email', '')
        
        logger.info(f"Pre-social login for {social_account.provider} account: {email}")
        
    except Exception as e:
        logger.error(f"Error in pre_social_login_handler: {e}")


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
            # Check if Student profile already exists
            if hasattr(user, 'student'):
                logger.info(f"Student profile already exists for: {user.username}")
                return
            
            # Get social account data
            social_account = sociallogin.account
            
            if social_account.provider == 'google':
                # Create Student profile using user fields (already set by adapter)
                student = Student.objects.create(
                    user_ptr=user,
                    username=user.username,
                    first_name=user.first_name or 'Not Set',
                    last_name=user.last_name or 'Not Set',
                    email=user.email or 'Not Set',
                    mobile_number='-',
                    gender='Not Set',
                )
                
                # Send welcome email
                try:
                    if student.email and student.email != 'Not Set':
                        send_welcome_mail(student.email, student.first_name)
                except Exception as email_error:
                    logger.warning(f"Failed to send welcome email: {email_error}")
                
                # Success message
                messages.success(request, f"🔥 Welcome to Angaar, {student.first_name}! Your account is ready.")
                
                logger.info(f"New student created via Google OAuth: {student.username} ({student.email})")
                
    except Exception as e:
        logger.error(f"Error in user_signed_up_handler: {e}", exc_info=True)


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


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Handle post-login actions and ensure proper redirect.
    This fires after a user is successfully logged in (including social login).
    """
    try:
        # Log the login
        if hasattr(user, 'student'):
            logger.info(f"Student logged in: {user.username}")
        elif hasattr(user, 'instructor'):
            logger.info(f"Instructor logged in: {user.username}")
        elif hasattr(user, 'administrator'):
            logger.info(f"Administrator logged in: {user.username}")
            
    except Exception as e:
        logger.error(f"Error in user_logged_in_handler: {e}")
