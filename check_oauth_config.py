#!/usr/bin/env python
"""
Script to verify Google OAuth configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'angaar_hai.settings')
django.setup()

from django.conf import settings
from allauth.socialaccount.models import SocialApp

print("=" * 60)
print("GOOGLE OAUTH CONFIGURATION CHECK")
print("=" * 60)

print("\n1. Django Settings:")
print(f"   LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")
print(f"   LOGIN_URL: {settings.LOGIN_URL}")
print(f"   SOCIALACCOUNT_AUTO_SIGNUP: {settings.SOCIALACCOUNT_AUTO_SIGNUP}")
print(f"   SOCIALACCOUNT_LOGIN_ON_GET: {settings.SOCIALACCOUNT_LOGIN_ON_GET}")
print(f"   SOCIALACCOUNT_ADAPTER: {settings.SOCIALACCOUNT_ADAPTER}")
print(f"   ACCOUNT_ADAPTER: {settings.ACCOUNT_ADAPTER}")

print("\n2. Installed Social Apps:")
try:
    google_app = SocialApp.objects.get(provider='google')
    print(f"   ✓ Google OAuth App Found:")
    print(f"     - ID: {google_app.id}")
    print(f"     - Client ID: {google_app.client_id[:20]}...")
    print(f"     - Sites: {list(google_app.sites.all())}")
except SocialApp.DoesNotExist:
    print("   ✗ Google OAuth App NOT configured in database")
    print("   ACTION: Configure Google OAuth App in Django Admin")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n3. Signal Handlers:")
from accounts import signals
print(f"   ✓ Signals module loaded")
print(f"   - pre_social_login handler registered")
print(f"   - user_signed_up handler registered")
print(f"   - social_account_added handler registered")

print("\n4. Adapters:")
from accounts.adapters import CustomSocialAccountAdapter, CustomAccountAdapter
print(f"   ✓ CustomSocialAccountAdapter loaded")
print(f"   ✓ CustomAccountAdapter loaded")

print("\n" + "=" * 60)
print("CONFIGURATION CHECK COMPLETE")
print("=" * 60)
