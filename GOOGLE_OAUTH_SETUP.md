# Google OAuth Setup Guide for Angaar Batch Portal

## Overview
This guide provides comprehensive instructions for setting up and configuring Google OAuth authentication for the Angaar Batch portal. The implementation uses Django Allauth with custom adapters and signal handlers for production-ready security and user management.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Google Cloud Console Setup](#google-cloud-console-setup)
3. [Django Configuration](#django-configuration)
4. [Database Setup](#database-setup)
5. [Testing the Integration](#testing-the-integration)
6. [Security Considerations](#security-considerations)
7. [Troubleshooting](#troubleshooting)
8. [Production Deployment](#production-deployment)

## Prerequisites

### Required Packages
Ensure these packages are installed (already in requirements.txt):
- `django-allauth==65.11.0`
- `django==5.2.5`

### Required Django Apps
Add these to your `INSTALLED_APPS` in settings.py:
```python
INSTALLED_APPS = [
    # ... other apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'django.contrib.sites',  # Required for allauth
]
```

## Google Cloud Console Setup

### 1. Create/Select Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project
3. Note your project ID

### 2. Enable APIs
Enable these APIs in your project:
- Google+ API (Legacy - still required for allauth)
- Google OAuth2 API
- People API (recommended)

### 3. Create OAuth 2.0 Credentials
1. Go to **Credentials** > **Create Credentials** > **OAuth 2.0 Client IDs**
2. Set **Application type** to "Web application"
3. Add **Authorized redirect URIs**:
   - Development: `http://localhost:8000/accounts/social/google/login/callback/`
   - Production: `https://yourdomain.com/accounts/social/google/login/callback/`
4. Save and copy **Client ID** and **Client Secret**

### 4. Configure OAuth Consent Screen
1. Go to **OAuth consent screen**
2. Choose **External** user type
3. Fill required fields:
   - App name: "Angaar Batch Portal"
   - User support email
   - Developer contact information
4. Add scopes: `email`, `profile`, `openid`
5. Add test users if in development

## Django Configuration

### 1. Settings Configuration
Add these settings to your `settings.py`:

```python
# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Site ID (required for allauth)
SITE_ID = 1

# Login/Logout URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Account settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Google handles email verification
ACCOUNT_USERNAME_REQUIRED = False    # We generate usernames automatically
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_UNIQUE_EMAIL = True

# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_LOGIN_ON_GET = False  # Security: prevent CSRF attacks
SOCIALACCOUNT_STORE_TOKENS = False  # Don't store tokens unless needed

# Custom adapters
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'

# Google OAuth Provider Configuration
SOCIALACCOUNT_PROVIDERS = {
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
}

# Optional: Use environment variables for sensitive data
import os
if os.getenv('GOOGLE_OAUTH_CLIENT_ID'):
    SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'] = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
if os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'):
    SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'] = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')

# Optional: Add security middleware
MIDDLEWARE = [
    # ... existing middleware
    'accounts.middleware.GoogleOAuthSecurityMiddleware',
    'accounts.middleware.SocialAccountErrorMiddleware',
    # 'accounts.middleware.RateLimitMiddleware',  # Uncomment for rate limiting
]
```

### 2. Environment Variables (Recommended)
Create a `.env` file or set environment variables:
```bash
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id_here
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret_here
```

## Database Setup

### 1. Run Migrations
```bash
python manage.py migrate
```

### 2. Create/Update Site
```bash
python manage.py shell
```

```python
from django.contrib.sites.models import Site
site = Site.objects.get(pk=1)
site.domain = 'localhost:8000'  # For development
site.name = 'Angaar Batch Portal'
site.save()
```

### 3. Create Social Application
Option A: Using Django Admin
1. Go to `/tera0mera1_dknaman/` (Django Admin)
2. Navigate to **Social Applications**
3. Click **Add Social Application**
4. Fill in:
   - Provider: Google
   - Name: Google OAuth
   - Client ID: (from Google Console)
   - Secret key: (from Google Console)
   - Sites: Select your site

Option B: Using Management Command
```bash
python manage.py validate_google_oauth --create-social-app
```

## Testing the Integration

### 1. Validate Configuration
```bash
python manage.py validate_google_oauth
```

### 2. Test OAuth Flow
1. Start development server: `python manage.py runserver`
2. Visit: `http://localhost:8000/accounts/login/`
3. Click "Login with Google" (uses URL: `/accounts/social/google/login/`)
4. Complete OAuth flow
5. Verify user creation in Django admin

**Alternative direct access:**
- Direct Google OAuth URL: `http://localhost:8000/accounts/social/google/login/`

### 3. Test User Creation
- New Google users should be created as Student profiles
- Existing users should be logged in without creating duplicates
- Staff emails should be blocked from Google login

### 4. Test Error Handling
- Try with unverified Google account
- Try with cancelled OAuth flow
- Try with network errors

## Security Considerations

### 1. Production Security
- Always use HTTPS in production
- Keep client secret secure and never commit to version control
- Use environment variables for sensitive data
- Regularly rotate OAuth credentials
- Monitor OAuth usage in Google Cloud Console

### 2. Rate Limiting
The implementation includes optional rate limiting middleware:
- Max 10 OAuth attempts per IP per hour
- Customize in `accounts/middleware.py`

### 3. Email Verification
- Google handles email verification
- Only verified Google accounts can sign up
- Staff emails are blocked from Google OAuth

### 4. CSRF Protection
- `SOCIALACCOUNT_LOGIN_ON_GET = False` prevents CSRF attacks
- Custom middleware adds security headers

## Troubleshooting

### Common Issues

#### 1. "Social application not found"
**Solution:** Create SocialApp in Django admin or run:
```bash
python manage.py validate_google_oauth --create-social-app
```

#### 2. "Redirect URI mismatch"
**Solution:** Check redirect URIs in Google Console match exactly:
- `http://localhost:8000/accounts/social/google/login/callback/`

#### 3. "Email not verified" error
**Solution:** Ensure Google account has verified email or update OAuth consent screen

#### 4. "Permission denied" error
**Solution:** Check OAuth consent screen configuration and scopes

#### 5. Users not being created as Students
**Solution:** Check signal handlers are properly imported in `accounts/apps.py`

### Debug Mode
Enable debug logging in settings.py:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'accounts': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'allauth': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Production Deployment

### 1. Update Site Configuration
```python
# In production settings
SITE_ID = 1

# Update site in database
from django.contrib.sites.models import Site
site = Site.objects.get(pk=1)
site.domain = 'yourdomain.com'
site.name = 'Angaar Batch Portal'
site.save()
```

### 2. Update Google Console
- Add production redirect URI: `https://yourdomain.com/accounts/social/google/login/callback/`
- Update OAuth consent screen with production domain
- Move from testing to production (if applicable)

### 3. Environment Variables
Set production environment variables:
```bash
export GOOGLE_OAUTH_CLIENT_ID=your_production_client_id
export GOOGLE_OAUTH_CLIENT_SECRET=your_production_client_secret
```

### 4. Security Checklist
- [ ] HTTPS enabled
- [ ] Environment variables set
- [ ] Site domain updated
- [ ] OAuth consent screen configured
- [ ] Rate limiting enabled (optional)
- [ ] Logging configured
- [ ] Error monitoring setup

## Useful Commands

```bash
# Validate OAuth configuration
python manage.py validate_google_oauth

# Create social app
python manage.py validate_google_oauth --create-social-app

# Check site configuration
python manage.py shell -c "from django.contrib.sites.models import Site; print(Site.objects.get(pk=1))"

# Test OAuth URLs
curl -I http://localhost:8000/accounts/social/google/login/
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Run the validation command
3. Check Django and allauth logs
4. Verify Google Console configuration

## Files Modified/Created

### New Files
- `accounts/signals.py` - OAuth signal handlers
- `accounts/adapters.py` - Custom allauth adapters
- `accounts/middleware.py` - Security and error handling middleware
- `accounts/google_oauth_settings.py` - Configuration template
- `accounts/management/commands/validate_google_oauth.py` - Validation command

### Modified Files
- `accounts/urls.py` - Updated URL patterns
- `accounts/apps.py` - Added signal registration
- `accounts/views.py` - Removed custom handler
- `templates/accounts/login.html` - Fixed Google login URL

This implementation provides a production-ready Google OAuth integration with comprehensive security measures, error handling, and user management specifically tailored for the Angaar Batch portal.
