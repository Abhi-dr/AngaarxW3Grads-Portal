"""
Google OAuth Settings Configuration Template
============================================

Add these settings to your settings.py file for proper Google OAuth integration.

IMPORTANT: Replace the placeholder values with your actual Google OAuth credentials.
Get your credentials from: https://console.developers.google.com/
"""

# Required Django Allauth Settings for Google OAuth
GOOGLE_OAUTH_SETTINGS = {
    # Authentication backends
    'AUTHENTICATION_BACKENDS': [
        'django.contrib.auth.backends.ModelBackend',
        'allauth.account.auth_backends.AuthenticationBackend',
    ],
    
    # Site ID (required for allauth)
    'SITE_ID': 1,
    
    # Login/Logout URLs
    'LOGIN_URL': '/accounts/login/',
    'LOGIN_REDIRECT_URL': '/dashboard/',  # Redirect to student dashboard after login
    'LOGOUT_REDIRECT_URL': '/',
    
    # Account settings
    'ACCOUNT_EMAIL_REQUIRED': True,
    'ACCOUNT_EMAIL_VERIFICATION': 'none',  # Google handles email verification
    'ACCOUNT_USERNAME_REQUIRED': False,    # We generate usernames automatically
    'ACCOUNT_AUTHENTICATION_METHOD': 'email',
    'ACCOUNT_UNIQUE_EMAIL': True,
    'ACCOUNT_USER_MODEL_USERNAME_FIELD': 'username',
    'ACCOUNT_USER_MODEL_EMAIL_FIELD': 'email',
    
    # Social account settings
    'SOCIALACCOUNT_AUTO_SIGNUP': True,
    'SOCIALACCOUNT_EMAIL_REQUIRED': True,
    'SOCIALACCOUNT_EMAIL_VERIFICATION': 'none',
    'SOCIALACCOUNT_QUERY_EMAIL': True,
    
    # Google OAuth Provider Configuration
    'SOCIALACCOUNT_PROVIDERS': {
        'google': {
            'SCOPE': [
                'profile',
                'email',
            ],
            'AUTH_PARAMS': {
                'access_type': 'online',
            },
            'OAUTH_PKCE_ENABLED': True,  # Enable PKCE for better security
            'FETCH_USERINFO': True,
            'APP': {
                'client_id': 'YOUR_GOOGLE_CLIENT_ID_HERE',
                'secret': 'YOUR_GOOGLE_CLIENT_SECRET_HERE',
                'key': ''
            }
        }
    },
    
    # Security settings
    'SOCIALACCOUNT_LOGIN_ON_GET': False,  # Prevent CSRF attacks
    'SOCIALACCOUNT_STORE_TOKENS': False,  # Don't store OAuth tokens unless needed
}

# Environment Variables Template
ENVIRONMENT_VARIABLES = """
# Add these to your .env file or environment variables:
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id_here
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret_here
"""

# Instructions for Google OAuth Setup
SETUP_INSTRUCTIONS = """
Google OAuth Setup Instructions:
================================

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select existing project
3. Enable Google+ API and Google OAuth2 API
4. Go to Credentials > Create Credentials > OAuth 2.0 Client IDs
5. Set Application type to "Web application"
6. Add authorized redirect URIs:
   - http://localhost:8000/accounts/social/google/login/callback/ (for development)
   - https://yourdomain.com/accounts/social/google/login/callback/ (for production)
7. Copy Client ID and Client Secret
8. Add them to your settings.py or environment variables

Security Considerations:
=======================
- Always use HTTPS in production
- Keep client secret secure and never commit to version control
- Use environment variables for sensitive data
- Enable PKCE for additional security
- Regularly rotate OAuth credentials
- Monitor OAuth usage in Google Cloud Console
"""

def validate_google_oauth_config():
    """
    Validate Google OAuth configuration.
    Call this function in your Django management command or admin.
    """
    from django.conf import settings
    
    errors = []
    
    # Check required settings
    if not hasattr(settings, 'SOCIALACCOUNT_PROVIDERS'):
        errors.append("SOCIALACCOUNT_PROVIDERS not configured")
    else:
        google_config = settings.SOCIALACCOUNT_PROVIDERS.get('google')
        if not google_config:
            errors.append("Google provider not configured in SOCIALACCOUNT_PROVIDERS")
        else:
            app_config = google_config.get('APP', {})
            if not app_config.get('client_id'):
                errors.append("Google client_id not configured")
            if not app_config.get('secret'):
                errors.append("Google client_secret not configured")
    
    # Check authentication backends
    auth_backends = getattr(settings, 'AUTHENTICATION_BACKENDS', [])
    if 'allauth.account.auth_backends.AuthenticationBackend' not in auth_backends:
        errors.append("Allauth authentication backend not configured")
    
    # Check installed apps
    installed_apps = getattr(settings, 'INSTALLED_APPS', [])
    required_apps = [
        'allauth',
        'allauth.account',
        'allauth.socialaccount',
        'allauth.socialaccount.providers.google',
    ]
    
    for app in required_apps:
        if app not in installed_apps:
            errors.append(f"Required app '{app}' not in INSTALLED_APPS")
    
    if errors:
        return False, errors
    else:
        return True, ["Google OAuth configuration is valid"]
