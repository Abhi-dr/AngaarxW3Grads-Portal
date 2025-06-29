from import_export import resources
from .models import Student

class StudentResource(resources.ModelResource):
    class Meta:
        model = Student
        exclude = ("password", "last_login", "is_superuser", "groups", "user_permissions", "is_staff", "is_active", "date_joined")

