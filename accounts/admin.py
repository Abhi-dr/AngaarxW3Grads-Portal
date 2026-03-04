from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportExportModelAdmin
from .resources import CustomUserResource
from .models import CustomUser, PasswordResetToken


# ── CustomUser (full admin with import/export) ─────────────────────────────
# Phase 2: Student/Instructor/Administrator proxy models removed.
# All user management is now through CustomUser, filtered by the `role` field.
# Use list_filter on 'role' to segment students / instructors / admins.
@admin.register(CustomUser)
class CustomUserAdmin(ImportExportModelAdmin, UserAdmin):
    resource_class = CustomUserResource

    list_display  = ("username", "email", "first_name", "last_name", "role", "is_active", "is_staff")
    list_filter   = ("role", "is_active", "is_staff", "college")
    search_fields = ("username", "email", "first_name", "last_name", "mobile_number")
    ordering      = ("-date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("role", "mobile_number", "gender", "college", "dob",
                                "profile_pic", "linkedin_id", "github_id")}),
        ("State",   {"fields": ("coins", "is_changed_password", "is_email_verified")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Profile", {"fields": ("role", "email", "mobile_number", "gender")}),
    )


admin.site.register(PasswordResetToken)
