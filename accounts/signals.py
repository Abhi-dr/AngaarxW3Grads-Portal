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

from .models import CustomUser

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
            # messages.success(request, f"Google account successfully linked to your profile!")
            pass
            
    except Exception as e:
        print(f"Error in social_account_added_handler: {e}")


@receiver(user_signed_up)
def user_signed_up_handler(sender, request, user, sociallogin=None, **kwargs):
    print(f"DEBUG: user_signed_up_handler called for {user.email}")
    """
    Handle user signup via social login.
    NOTE: In Phase 2, CustomSocialAccountAdapter (adapters.py) handles setting defaults
    and saving the CustomUser instance. We no longer use proxy class conversions here.
    """
    if not sociallogin:
        return
        
    if sociallogin.account.provider == 'google':
        # Welcome email handled by adapter, we just show a message.
        messages.success(request, f"🔥 Welcome to Angaar, {user.first_name}! Your account is ready.")
        logger.info(f"New student verified via Google OAuth: {user.username} ({user.email})")


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
    print(f"DEBUG: user_logged_in_handler called for {user.email}")
    """
    Handle post-login actions and ensure proper redirect.
    This fires after a user is successfully logged in (including social login).
    """
    try:
        # Log the login
        if getattr(user, 'role', None) == 'student':
            logger.info(f"Student logged in: {user.username}")
        elif getattr(user, 'role', None) == 'instructor':
            logger.info(f"Instructor logged in: {user.username}")
        elif getattr(user, 'role', None) == 'admin':
            logger.info(f"Administrator logged in: {user.username}")
            
    except Exception as e:
        logger.error(f"Error in user_logged_in_handler: {e}")
