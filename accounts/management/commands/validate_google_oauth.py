from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from accounts.google_oauth_settings import validate_google_oauth_config


class Command(BaseCommand):
    help = 'Validate Google OAuth configuration and setup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix common configuration issues',
        )
        parser.add_argument(
            '--create-social-app',
            action='store_true',
            help='Create SocialApp entry for Google OAuth',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('🔍 Validating Google OAuth Configuration...'))
        
        # Validate configuration
        is_valid, messages = validate_google_oauth_config()
        
        if is_valid:
            self.stdout.write(self.style.SUCCESS('✅ Basic configuration is valid'))
        else:
            self.stdout.write(self.style.ERROR('❌ Configuration issues found:'))
            for message in messages:
                self.stdout.write(self.style.ERROR(f'  • {message}'))
        
        # Check Site configuration
        self.check_site_configuration()
        
        # Check SocialApp configuration
        self.check_social_app_configuration(options.get('create_social_app', False))
        
        # Check environment variables
        self.check_environment_variables()
        
        # Provide setup instructions if needed
        if not is_valid or options.get('fix'):
            self.provide_setup_instructions()

    def check_site_configuration(self):
        """Check Django Sites framework configuration"""
        self.stdout.write('\n🌐 Checking Site Configuration...')
        
        try:
            site_id = getattr(settings, 'SITE_ID', None)
            if not site_id:
                self.stdout.write(self.style.WARNING('  ⚠️  SITE_ID not set in settings'))
                return
            
            site = Site.objects.get(pk=site_id)
            self.stdout.write(self.style.SUCCESS(f'  ✅ Site configured: {site.domain} ({site.name})'))
            
            if site.domain == 'example.com':
                self.stdout.write(self.style.WARNING('  ⚠️  Site domain is still example.com - update for production'))
                
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'  ❌ Site with ID {site_id} does not exist'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error checking site: {e}'))

    def check_social_app_configuration(self, create_if_missing=False):
        """Check SocialApp configuration for Google"""
        self.stdout.write('\n📱 Checking SocialApp Configuration...')
        
        try:
            google_apps = SocialApp.objects.filter(provider='google')
            
            if not google_apps.exists():
                self.stdout.write(self.style.WARNING('  ⚠️  No Google SocialApp found'))
                if create_if_missing:
                    self.create_google_social_app()
                else:
                    self.stdout.write(self.style.HTTP_INFO('  💡 Run with --create-social-app to create one'))
                return
            
            for app in google_apps:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Google SocialApp found: {app.name}'))
                
                # Check if app has required fields
                if not app.client_id:
                    self.stdout.write(self.style.ERROR('    ❌ Client ID is missing'))
                else:
                    self.stdout.write(self.style.SUCCESS('    ✅ Client ID is set'))
                
                if not app.secret:
                    self.stdout.write(self.style.ERROR('    ❌ Client Secret is missing'))
                else:
                    self.stdout.write(self.style.SUCCESS('    ✅ Client Secret is set'))
                
                # Check sites
                sites = app.sites.all()
                if not sites:
                    self.stdout.write(self.style.WARNING('    ⚠️  No sites associated with this app'))
                else:
                    for site in sites:
                        self.stdout.write(self.style.SUCCESS(f'    ✅ Associated with site: {site.domain}'))
                        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error checking SocialApp: {e}'))

    def create_google_social_app(self):
        """Create a Google SocialApp entry"""
        try:
            site = Site.objects.get(pk=getattr(settings, 'SITE_ID', 1))
            
            app = SocialApp.objects.create(
                provider='google',
                name='Google OAuth',
                client_id='YOUR_GOOGLE_CLIENT_ID_HERE',
                secret='YOUR_GOOGLE_CLIENT_SECRET_HERE',
            )
            app.sites.add(site)
            
            self.stdout.write(self.style.SUCCESS('  ✅ Google SocialApp created'))
            self.stdout.write(self.style.WARNING('  ⚠️  Remember to update Client ID and Secret in Django Admin'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error creating SocialApp: {e}'))

    def check_environment_variables(self):
        """Check for environment variables"""
        self.stdout.write('\n🔐 Checking Environment Variables...')
        
        import os
        
        env_vars = [
            'GOOGLE_OAUTH_CLIENT_ID',
            'GOOGLE_OAUTH_CLIENT_SECRET',
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                self.stdout.write(self.style.SUCCESS(f'  ✅ {var} is set'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠️  {var} is not set'))

    def provide_setup_instructions(self):
        """Provide setup instructions"""
        self.stdout.write('\n📋 Setup Instructions:')
        self.stdout.write('=' * 50)
        
        instructions = """
1. Google Cloud Console Setup:
   • Go to https://console.cloud.google.com/
   • Create/select a project
   • Enable Google+ API and OAuth2 API
   • Create OAuth 2.0 credentials
   • Add redirect URIs:
     - http://localhost:8000/accounts/social/google/login/callback/
     - https://yourdomain.com/accounts/social/google/login/callback/

2. Django Configuration:
   • Update SITE_ID and Site domain in Django admin
   • Create SocialApp in Django admin or run:
     python manage.py validate_google_oauth --create-social-app
   • Add Client ID and Secret to SocialApp

3. Environment Variables (Optional):
   • Set GOOGLE_OAUTH_CLIENT_ID
   • Set GOOGLE_OAUTH_CLIENT_SECRET

4. Test the Integration:
   • Visit /accounts/social/google/login/
   • Complete OAuth flow
   • Check user creation in Django admin
"""
        
        self.stdout.write(instructions)
        
        self.stdout.write('\n🔗 Useful URLs:')
        self.stdout.write('  • Django Admin: /tera0mera1_dknaman/')
        self.stdout.write('  • Google Login: /accounts/social/google/login/')
        self.stdout.write('  • Login Page: /accounts/login/')
        
        self.stdout.write(self.style.HTTP_INFO('\n💡 Run this command again after configuration to validate setup'))
