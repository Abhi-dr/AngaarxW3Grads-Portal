from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .resources import StudentResource
from .models import Student, Instructor

    
class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ("username", "first_name", "last_name", "email")
    search_fields = ("username", "first_name", "last_name", "email", "mobile_number")
    list_filter = ("college", "is_changed_password")
    exclude = ("password", "last_login", "is_superuser", "groups", "user_permissions", "is_staff", "is_active", "date_joined")


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ("username", "first_name", "last_name", "email")
    exclude = ("password", "last_login", "is_superuser", "groups", "user_permissions", "is_active", "date_joined")


admin.site.register(Student, StudentAdmin)
