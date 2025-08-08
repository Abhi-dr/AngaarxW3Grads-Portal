from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # This method is called once when Django starts.
        # We will apply our patch here.
        
        from allauth.socialaccount.models import SocialAccount

        # 1. Store the original __str__ method
        original_social_account_str = SocialAccount.__str__

        # 2. Define our new __str__ method
        def patched_social_account_str(self):
            # Call the original method and explicitly convert its result to a string
            return str(original_social_account_str(self))

        # 3. Replace the original method with our new one
        SocialAccount.__str__ = patched_social_account_str

