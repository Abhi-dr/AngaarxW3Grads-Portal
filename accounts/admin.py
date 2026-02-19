from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportExportModelAdmin
from .resources import StudentResource
from .models import CustomUser, Student, Instructor, Administrator, PasswordResetToken


# ── CustomUser (full admin, shown as "Users") ──────────────────────────────
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
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


# ── Student proxy (Import/Export enabled) ──────────────────────────────────
@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display   = ("username", "first_name", "last_name", "email", "mobile_number", "college")
    search_fields  = ("username", "first_name", "last_name", "email", "mobile_number")
    list_filter    = ("college", "is_changed_password", "is_active")
    exclude        = ("password", "last_login", "is_superuser", "groups",
                      "user_permissions", "is_staff", "date_joined", "role")


# ── Instructor proxy ───────────────────────────────────────────────────────
@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display  = ("username", "first_name", "last_name", "email")
    search_fields = ("username", "email", "first_name", "last_name")
    exclude       = ("password", "last_login", "is_superuser", "groups",
                     "user_permissions", "date_joined", "role")


# ── Administrator proxy ────────────────────────────────────────────────────
@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    list_display  = ("username", "first_name", "last_name", "email")
    search_fields = ("username", "email", "first_name", "last_name")
    exclude       = ("password", "last_login", "is_superuser", "groups",
                     "user_permissions", "date_joined", "role")


admin.site.register(PasswordResetToken)
