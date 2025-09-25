from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class GoogleOAuthSecurityMiddleware:
    """
    Middleware to handle Google OAuth security and error handling.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Pre-process request
        if self.is_google_oauth_request(request):
            # Add security headers for OAuth requests
            response = self.get_response(request)
            response = self.add_security_headers(response)
            return response
        
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Handle exceptions during OAuth flow"""
        if self.is_google_oauth_request(request):
            logger.error(f"OAuth error: {exception}", exc_info=True)
            messages.error(request, "An error occurred during Google login. Please try again.")
            return redirect('login')
        return None

    def is_google_oauth_request(self, request):
        """Check if this is a Google OAuth related request"""
        oauth_paths = [
            '/accounts/social/google/',
            '/accounts/social/login/google/',
            '/accounts/social/signup/google/',
        ]
        return any(request.path.startswith(path) for path in oauth_paths)

    def add_security_headers(self, response):
        """Add security headers to OAuth responses"""
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response


class SocialAccountErrorMiddleware:
    """
    Middleware to handle social account errors gracefully.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Handle social account related exceptions"""
        # Handle common allauth exceptions
        exception_name = exception.__class__.__name__
        
        if 'allauth' in str(type(exception).__module__):
            logger.error(f"Social auth error: {exception}", exc_info=True)
            
            error_messages = {
                'ImmediateHttpResponse': "Authentication was cancelled. Please try again.",
                'AuthenticationError': "Authentication failed. Please check your credentials.",
                'PermissionDenied': "Permission denied during authentication.",
                'ValidationError': "Invalid data received during authentication.",
            }
            
            message = error_messages.get(exception_name, "An error occurred during social login.")
            messages.error(request, message)
            
            return redirect('login')
        
        return None


def handle_oauth_error(request, error_type, error_message=None):
    """
    Centralized OAuth error handling function.
    """
    error_messages = {
        'cancelled': "Google login was cancelled. Please try again.",
        'denied': "Access was denied. Please grant necessary permissions.",
        'invalid_request': "Invalid request. Please try again.",
        'server_error': "Server error occurred. Please try again later.",
        'temporarily_unavailable': "Service temporarily unavailable. Please try again later.",
        'email_not_verified': "Please verify your email with Google before logging in.",
        'email_already_exists': "An account with this email already exists. Please use regular login.",
        'provider_not_supported': "Only Google login is supported for students.",
    }
    
    message = error_message or error_messages.get(error_type, "An error occurred during login.")
    messages.error(request, message)
    
    logger.warning(f"OAuth error handled: {error_type} - {message}")
    
    return redirect('login')


class RateLimitMiddleware:
    """
    Simple rate limiting middleware for OAuth endpoints.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.oauth_attempts = {}  # In production, use Redis or database

    def __call__(self, request):
        if self.is_oauth_request(request):
            client_ip = self.get_client_ip(request)
            
            # Check rate limit (max 10 attempts per hour)
            if self.is_rate_limited(client_ip):
                messages.error(request, "Too many login attempts. Please try again later.")
                return redirect('login')
            
            # Record attempt
            self.record_attempt(client_ip)
        
        response = self.get_response(request)
        return response

    def is_oauth_request(self, request):
        """Check if this is an OAuth request"""
        return '/accounts/social/' in request.path

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_rate_limited(self, client_ip):
        """Check if client is rate limited"""
        import time
        current_time = time.time()
        
        if client_ip not in self.oauth_attempts:
            return False
        
        # Remove attempts older than 1 hour
        self.oauth_attempts[client_ip] = [
            attempt_time for attempt_time in self.oauth_attempts[client_ip]
            if current_time - attempt_time < 3600
        ]
        
        # Check if more than 10 attempts in last hour
        return len(self.oauth_attempts[client_ip]) >= 10

    def record_attempt(self, client_ip):
        """Record OAuth attempt"""
        import time
        current_time = time.time()
        
        if client_ip not in self.oauth_attempts:
            self.oauth_attempts[client_ip] = []
        
        self.oauth_attempts[client_ip].append(current_time)
