from import_export import resources
from .models import CustomUser

# Renamed from StudentResource → CustomUserResource after proxy model removal (Phase 2)
class CustomUserResource(resources.ModelResource):
    class Meta:
        model = CustomUser
        exclude = ("password", "last_login", "is_superuser", "groups", "user_permissions", "is_staff", "is_active", "date_joined")
