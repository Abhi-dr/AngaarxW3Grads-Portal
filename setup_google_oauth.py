#!/usr/bin/env python
"""
Quick setup script for Google OAuth configuration.
Run this script to quickly configure Google OAuth for development.

Usage:
    python setup_google_oauth.py --client-id YOUR_CLIENT_ID --client-secret YOUR_SECRET
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'angaar_hai.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings
import argparse


def setup_site():
    """Setup site configuration for development"""
    try:
        site = Site.objects.get(pk=getattr(settings, 'SITE_ID', 1))
        site.domain = 'localhost:8000'
        site.name = 'Angaar Batch Portal (Dev)'
        site.save()
        print(f"✅ Site configured: {site.domain}")
        return site
    except Site.DoesNotExist:
        site = Site.objects.create(
            pk=getattr(settings, 'SITE_ID', 1),
            domain='localhost:8000',
            name='Angaar Batch Portal (Dev)'
        )
        print(f"✅ Site created: {site.domain}")
        return site


def setup_social_app(client_id, client_secret):
    """Setup Google Social App"""
    try:
        # Check if Google app already exists
        app = SocialApp.objects.filter(provider='google').first()
        if app:
            app.client_id = client_id
            app.secret = client_secret
            app.save()
            print(f"✅ Updated existing Google SocialApp: {app.name}")
        else:
            # Create new Google app
            app = SocialApp.objects.create(
                provider='google',
                name='Google OAuth (Dev)',
                client_id=client_id,
                secret=client_secret,
            )
            print(f"✅ Created Google SocialApp: {app.name}")
        
        # Associate with site
        site = Site.objects.get(pk=getattr(settings, 'SITE_ID', 1))
        app.sites.add(site)
        print(f"✅ Associated with site: {site.domain}")
        
        return app
        
    except Exception as e:
        print(f"❌ Error setting up SocialApp: {e}")
        return None


def validate_configuration():
    """Validate the OAuth configuration"""
    print("\n🔍 Validating configuration...")
    
    # Check required settings
    checks = [
        ('SITE_ID', hasattr(settings, 'SITE_ID')),
        ('SOCIALACCOUNT_PROVIDERS', hasattr(settings, 'SOCIALACCOUNT_PROVIDERS')),
        ('AUTHENTICATION_BACKENDS', 'allauth.account.auth_backends.AuthenticationBackend' in getattr(settings, 'AUTHENTICATION_BACKENDS', [])),
    ]
    
    for setting, is_valid in checks:
        status = "✅" if is_valid else "❌"
        print(f"  {status} {setting}")
    
    # Check SocialApp
    google_apps = SocialApp.objects.filter(provider='google')
    if google_apps.exists():
        app = google_apps.first()
        print(f"  ✅ Google SocialApp exists: {app.name}")
        print(f"    Client ID: {app.client_id[:10]}...")
        print(f"    Sites: {', '.join([site.domain for site in app.sites.all()])}")
    else:
        print("  ❌ No Google SocialApp found")


def create_env_file(client_id, client_secret):
    """Create .env file with OAuth credentials"""
    env_content = f"""# Google OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID={client_id}
GOOGLE_OAUTH_CLIENT_SECRET={client_secret}

# Add other environment variables as needed
# DEBUG=True
# SECRET_KEY=your-secret-key
"""
    
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"⚠️  {env_file} already exists. Skipping creation.")
    else:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Created {env_file} with OAuth credentials")


def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup Complete!")
    print("\nNext Steps:")
    print("1. Start the development server:")
    print("   python manage.py runserver")
    print("\n2. Test Google OAuth:")
    print("   http://localhost:8000/accounts/login/")
    print("\n3. Validate configuration:")
    print("   python manage.py validate_google_oauth")
    print("\n4. Check Django Admin:")
    print("   http://localhost:8000/tera0mera1_dknaman/")
    print("\n5. Make sure your Google Console redirect URI is:")
    print("   http://localhost:8000/accounts/social/google/login/callback/")


def main():
    parser = argparse.ArgumentParser(description='Setup Google OAuth for Angaar Batch Portal')
    parser.add_argument('--client-id', required=True, help='Google OAuth Client ID')
    parser.add_argument('--client-secret', required=True, help='Google OAuth Client Secret')
    parser.add_argument('--skip-env', action='store_true', help='Skip creating .env file')
    parser.add_argument('--production', action='store_true', help='Setup for production')
    
    args = parser.parse_args()
    
    print("🚀 Setting up Google OAuth for Angaar Batch Portal...")
    
    # Setup site
    if args.production:
        print("⚠️  Production setup not implemented in this script.")
        print("   Please follow the production deployment guide in GOOGLE_OAUTH_SETUP.md")
        return
    else:
        site = setup_site()
    
    # Setup social app
    app = setup_social_app(args.client_id, args.client_secret)
    if not app:
        print("❌ Failed to setup SocialApp. Exiting.")
        return
    
    # Create .env file
    if not args.skip_env:
        create_env_file(args.client_id, args.client_secret)
    
    # Validate configuration
    validate_configuration()
    
    # Print next steps
    print_next_steps()


if __name__ == '__main__':
    main()
