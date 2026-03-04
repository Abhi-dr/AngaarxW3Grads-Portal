"""
Email-only authentication backend.

This replaces Django's default ModelBackend to ensure users can ONLY
log in using their email address, not their username.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailOnlyBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL using email only.
    Rejects any login attempt that uses a username instead of an email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        # Reject if no email-like value is provided
        if username is None:
            username = kwargs.get(UserModel.EMAIL_FIELD)

        if username is None or password is None:
            return None

        try:
            # Look up by email (case-insensitive)
            user = UserModel.objects.get(email__iexact=username)
        except UserModel.DoesNotExist:
            # Run the default password hasher to prevent timing attacks
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            # If somehow two accounts share an email, deny login
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
