# Required Settings Fixes for Google OAuth

## Issues Found in Your Settings:

1. **Missing `django.contrib.sites`** - This is causing the RuntimeError
2. **Incorrect LOGIN_REDIRECT_URL** - Points to removed handler
3. **Security Issue** - `SOCIALACCOUNT_LOGIN_ON_GET = True` is unsafe
4. **Missing Account Settings** - Need additional allauth configurations

## Required Changes:

### 1. Add Missing App to INSTALLED_APPS

Add `'django.contrib.sites'` to your INSTALLED_APPS:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # ADD THIS LINE
    
    'accounts.apps.AccountsConfig',
    # ... rest of your apps
]
```

### 2. Update AllAuth Settings Section

Replace your entire "AllAuth Settings" section with this:

```python
# =================== AllAuth Settings =========================

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Custom adapters
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'

# Login/Logout URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'  # Fixed: was pointing to removed handler
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
SOCIALACCOUNT_LOGIN_ON_GET = False   # Fixed: was True (security risk)
SOCIALACCOUNT_STORE_TOKENS = False   # Don't store tokens unless needed

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
        'OAUTH_PKCE_ENABLED': True,  # Added: Better security
        'FETCH_USERINFO': True,      # Added: Get user info
        'APP': {
            'client_id': os.getenv("GOOGLE_CLIENT_ID"),
            'secret': os.getenv("GOOGLE_SECRET"),
            'key': ''
        }
    }
}
```

### 3. Optional: Add Security Middleware

Add these to your MIDDLEWARE (optional but recommended):

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    'corsheaders.middleware.CorsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    
    # Optional: Add these for better OAuth security
    'accounts.middleware.GoogleOAuthSecurityMiddleware',
    'accounts.middleware.SocialAccountErrorMiddleware',
    
    'angaar_hai.middleware.MaintenanceModeMiddleware',
]
```

## Summary of Changes:

1. ✅ **Add `django.contrib.sites`** to INSTALLED_APPS
2. ✅ **Fix LOGIN_REDIRECT_URL** from `/accounts/social/google/handler/` to `/dashboard/`
3. ✅ **Fix Security Issue** - Change `SOCIALACCOUNT_LOGIN_ON_GET` from `True` to `False`
4. ✅ **Add Missing Settings** - Added proper account and social account configurations
5. ✅ **Add Security Features** - Added PKCE and other security enhancements

## After Making Changes:

1. **Run migrations:**
   ```bash
   python3 manage.py migrate
   ```

2. **Test the validation command:**
   ```bash
   python3 manage.py validate_google_oauth
   ```

3. **Create/Update Site object:**
   ```bash
   python3 manage.py shell -c "
   from django.contrib.sites.models import Site
   site, created = Site.objects.get_or_create(pk=1)
   site.domain = 'localhost:8000'
   site.name = 'Angaar Batch Portal'
   site.save()
   print(f'Site configured: {site.domain}')
   "
   ```

Make these changes and the Google OAuth should work properly!
