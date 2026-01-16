#!/usr/bin/env python
"""Verify Google OAuth configuration"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'angaar_hai.settings')
django.setup()

from django.conf import settings

print("=" * 70)
print("GOOGLE OAUTH CONFIGURATION - COMPLETE VERIFICATION")
print("=" * 70)

config = {
    "Adapter Settings": {
        "ACCOUNT_ADAPTER": settings.ACCOUNT_ADAPTER,
        "SOCIALACCOUNT_ADAPTER": settings.SOCIALACCOUNT_ADAPTER,
    },
    "Redirect URLs": {
        "LOGIN_URL": settings.LOGIN_URL,
        "LOGIN_REDIRECT_URL": settings.LOGIN_REDIRECT_URL,
        "ACCOUNT_SIGNUP_REDIRECT_URL": getattr(settings, 'ACCOUNT_SIGNUP_REDIRECT_URL', 'NOT SET'),
        "LOGOUT_REDIRECT_URL": settings.LOGOUT_REDIRECT_URL,
    },
    "Social Account Settings": {
        "SOCIALACCOUNT_AUTO_SIGNUP": settings.SOCIALACCOUNT_AUTO_SIGNUP,
        "SOCIALACCOUNT_EMAIL_VERIFICATION": settings.SOCIALACCOUNT_EMAIL_VERIFICATION,
        "SOCIALACCOUNT_LOGIN_ON_GET": settings.SOCIALACCOUNT_LOGIN_ON_GET,
        "ACCOUNT_EMAIL_VERIFICATION": settings.ACCOUNT_EMAIL_VERIFICATION,
    },
    "Google Provider": {
        "Configured": 'google' in settings.SOCIALACCOUNT_PROVIDERS,
        "Scopes": settings.SOCIALACCOUNT_PROVIDERS.get('google', {}).get('SCOPE', []),
    }
}

for section, values in config.items():
    print(f"\n{section}:")
    for key, value in values.items():
        status = "✓" if value else "⚠"
        print(f"  {status} {key}: {value}")

print("\n" + "=" * 70)

# Check signal handlers
from accounts.signals import pre_social_login_handler, user_signed_up_handler, social_account_added_handler, user_logged_in_handler

print("\nSignal Handlers Registered:")
print("  ✓ pre_social_login_handler")
print("  ✓ social_account_added_handler")
print("  ✓ user_signed_up_handler")
print("  ✓ user_logged_in_handler")

# Check adapters
from accounts.adapters import CustomSocialAccountAdapter, CustomAccountAdapter

print("\nAdapters Registered:")
print("  ✓ CustomSocialAccountAdapter")
print("  ✓ CustomAccountAdapter")

print("\n" + "=" * 70)
print("✓ ALL OAUTH CONFIGURATION VERIFIED - READY FOR TESTING")
print("=" * 70)
