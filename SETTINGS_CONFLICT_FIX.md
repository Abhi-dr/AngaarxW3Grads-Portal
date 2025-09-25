# Fix for MultipleObjectsReturned Error

## Problem
You have **both** a SocialApp in the database AND an APP configuration in your settings.py. This creates a conflict because allauth finds multiple sources for Google OAuth configuration.

## Solution
Remove the APP configuration from your SOCIALACCOUNT_PROVIDERS setting since you're using the database approach (SocialApp).

## Required Change in settings.py

**Replace this section in your settings.py:**

```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv("GOOGLE_CLIENT_ID"),
            'secret': os.getenv("GOOGLE_SECRET"),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}
```

**With this (remove the APP section):**

```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,  # Better security
        'FETCH_USERINFO': True,      # Get user info
    }
}
```

## Why This Fixes the Issue

- **Database Approach**: SocialApp objects in Django admin (what we set up)
- **Settings Approach**: APP configuration in settings.py (what was causing conflict)
- **Allauth Rule**: Use either database OR settings, not both

Since we already have the SocialApp configured in the database with your real Google credentials, we should remove the APP configuration from settings to avoid the conflict.

## After Making the Change

1. **Restart your Django server**
2. **Test the Google login**: `http://localhost:8000/accounts/login/`
3. **The error should be resolved**

The SocialApp in your database already has the correct credentials:
- Client ID: 869693616227-n6c803j4adn6ai62eb198ofl1g5vutlq.apps.googleusercontent.com
- Secret: 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

So removing the APP configuration will make allauth use only the database configuration.
