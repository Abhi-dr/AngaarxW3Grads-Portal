"""
Google OAuth Settings Configuration
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
