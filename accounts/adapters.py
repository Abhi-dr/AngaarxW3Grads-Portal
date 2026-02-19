from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ValidationError
import logging

from .models import CustomUser

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for additional account management control.
    """

    def respond_user_inactive(self, request, user):
        """
        Redirect inactive users to the verification sent page.
        Only resend verification email for manual registrations, NOT for Google OAuth.
        """
        from .views import send_verification_mail
        from django.shortcuts import render
        from allauth.socialaccount.models import SocialAccount

        try:
            has_google_account = SocialAccount.objects.filter(
                user=user,
                provider='google'
            ).exists()

            if not has_google_account:
                send_verification_mail(user, request)
                logger.info(f"Resent verification email to inactive user: {user.email}")
            else:
                # Google OAuth user — activate directly
                logger.info(f"Activating Google OAuth user: {user.email}")
                user.is_active = True
                user.save()
        except Exception as e:
            logger.error(f"Failed to handle inactive user: {e}")

        return render(request, "accounts/verification_sent.html", {"email": user.email})

    def add_message(self, request, level, message_template, message_context=None, extra_tags=''):
        """Suppress the 'Successfully signed in as...' message."""
        if message_template == 'account/messages/logged_in.txt':
            return
        super().add_message(request, level, message_template, message_context, extra_tags)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for Google OAuth handling.
    All references updated from Student/Instructor/Administrator → CustomUser.
    """

    def is_open_for_signup(self, request, sociallogin):
        """Only allow Google provider with verified email."""
        if sociallogin.account.provider != 'google':
            return False
        # Temporarily lenient for debugging
        return True

    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via Google,
        before the login is actually processed.
        """
        try:
            user_data = sociallogin.account.extra_data
            email = user_data.get('email', '').lower()
            provider = sociallogin.account.provider

            # Only allow Google
            if provider != 'google':
                messages.error(request, "Only Google login is supported.")
                raise ImmediateHttpResponse(redirect('login'))

            # Require verified email
            if not user_data.get('email_verified', False):
                messages.error(request, "Please verify your email with Google before logging in.")
                raise ImmediateHttpResponse(redirect('login'))

            # Block staff (instructors/admins) from Google login
            if CustomUser.objects.filter(email=email, role__in=['instructor', 'admin']).exists():
                messages.error(request, "Staff accounts must use username/password login.")
                raise ImmediateHttpResponse(redirect('login'))

            # Existing student — bind sociallogin to them
            if CustomUser.objects.filter(email=email, role='student').exists():
                existing_user = CustomUser.objects.get(email=email)

                if not existing_user.is_active:
                    existing_user.is_active = True
                    existing_user.save()
                    logger.info(f"Activated previously inactive student via Google: {email}")

                sociallogin.user = existing_user
                logger.info(f"Existing student logging in via Google: {email}")

            # Zombie user — CustomUser exists but no role assigned (edge case)
            elif CustomUser.objects.filter(email=email).exists():
                user = CustomUser.objects.get(email=email)
                user.role = 'student'
                if not user.mobile_number:
                    user.mobile_number = '-'
                if not user.gender:
                    user.gender = 'Not Set'
                user.save()
                sociallogin.user = user
                logger.info(f"Repaired zombie user account for Google login: {email}")

            else:
                # New user — allow proceed to save_user
                logger.info(f"New student signup via Google: {email}")

        except ImmediateHttpResponse:
            raise
        except Exception as e:
            logger.error(f"Error in pre_social_login: {e}", exc_info=True)
            messages.error(request, "An error occurred during login. Please try again.")
            raise ImmediateHttpResponse(redirect('login'))

    def save_user(self, request, sociallogin, form=None):
        """
        Save new user from Google OAuth. Creates CustomUser with role='student'.
        """
        try:
            user_data = sociallogin.account.extra_data

            email = user_data.get('email', '').lower().strip()
            if not email:
                raise ValidationError("Email is required for Google OAuth registration.")

            user = CustomUser()
            user.username = self.generate_unique_username(user_data)
            user.first_name = user_data.get('given_name', '').strip() or 'Not Set'
            user.last_name  = user_data.get('family_name', '').strip() or ''
            user.email      = email
            user.role       = 'student'

            # Google-verified accounts are active immediately
            user.is_active       = True
            user.is_staff        = False
            user.is_superuser    = False

            # Student-specific defaults
            user.mobile_number       = '-'
            user.gender              = 'Not Set'
            user.college             = None
            user.dob                 = None
            user.is_changed_password = False
            user.profile_pic         = '/student_profile/default.jpg'
            user.linkedin_id         = None
            user.github_id           = None
            user.coins               = 100
            user.is_email_verified   = True  # Google already verified

            user.save()
            sociallogin.user = user

            # Send welcome email
            try:
                from .views import send_welcome_mail
                if user.email:
                    send_welcome_mail(user.email, user.first_name)
            except Exception as email_error:
                logger.error(f"Failed to send welcome email: {email_error}", exc_info=True)

            logger.info(f"CustomUser created from Google OAuth: {user.username} ({user.email})")
            return user

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error in save_user: {e}", exc_info=True)
            raise ValidationError(f"Failed to create user account: {str(e)}")

    def generate_unique_username(self, user_data):
        """Generate a unique username from Google user data."""
        import re
        first_name   = user_data.get('given_name', '') or 'user'
        base_username = re.sub(r'[^a-zA-Z0-9]', '', first_name.lower().strip()) or 'user'

        username = base_username
        counter  = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username

    def get_login_redirect_url(self, request):
        """Redirect Google OAuth users to student dashboard."""
        try:
            return reverse('student')
        except Exception as e:
            logger.error(f"Error getting login redirect URL: {e}")
            return '/dashboard/'

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """Handle authentication errors gracefully."""
        logger.error(f"Social authentication error for {provider_id}: {error}", exc_info=True)

        error_messages = {
            'cancelled':       "Google login was cancelled.",
            'denied':          "Access was denied. Please grant necessary permissions.",
            'invalid_request': "Invalid request during authentication.",
            'server_error':    "Server error occurred during authentication.",
        }
        messages.error(request, error_messages.get(error, "An error occurred during Google login."))
        return redirect('login')

    def is_auto_signup_allowed(self, request, sociallogin):
        """Allow automatic signup for Google accounts with verified email."""
        if sociallogin.account.provider == 'google':
            return sociallogin.account.extra_data.get('email_verified', False)
        return False

    def get_connect_redirect_url(self, request, socialaccount):
        return reverse('student')
