from django.contrib import admin
from .models import Notification, Anonymous_Message, Feedback, AIQuestion, CourseRegistration, CourseSheet
from .hackathon_models import HackathonTeam, TeamMember, JoinRequest, TeamInvite
from .event_models import Event, Certificate, CertificateTemplate

from django.contrib import admin
from import_export.admin import ImportMixin
from import_export import resources, fields
from import_export.results import RowResult
from accounts.models import Student
from import_export.widgets import ForeignKeyWidget


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'expiration_date', 'is_fixed', 'is_alert')
    list_filter = ('type', 'is_fixed')
    search_fields = ('title', 'description')
    
@admin.register(Anonymous_Message)
class Anonymous_MessageAdmin(admin.ModelAdmin):
    list_display = ('student', 'instructor', 'message', "is_replied")
    search_fields = ('student', 'instructor', 'message')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject')
    search_fields = ('student',)

@admin.register(AIQuestion)
class AIQuestionAdmin(admin.ModelAdmin):
    list_display = ('student', 'instructor', 'question')
    search_fields = ('student', 'question')

# Register Hackathon models
@admin.register(HackathonTeam)
class HackathonTeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'leader', 'status', 'members_limit', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'description', 'leader__username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('team', 'student', 'joined_at')
    list_filter = ('joined_at',)
    search_fields = ('team__name', 'student__username')
    readonly_fields = ('joined_at',)

@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):
    list_display = ('team', 'student', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('team__name', 'student__username', 'message')
    readonly_fields = ('created_at',)
    
@admin.register(TeamInvite)
class TeamInviteAdmin(admin.ModelAdmin):
    list_display = ('team', 'student', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('team__name', 'student__username')
    readonly_fields = ('created_at',)
    
# ===========================================================================================
# ===========================================================================================
# ===========================================================================================

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib import messages
from .models import Course, Assignment, AssignmentSubmission


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
    list_per_page = 25

@admin.register(CourseRegistration)
class CourseRegistrationAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'registration_date']
    list_filter = ['course', 'registration_date']

@admin.register(CourseSheet)
class CourseSheetAdmin(admin.ModelAdmin):
    list_display = ["name",]

class AssignmentInline(admin.TabularInline):
    """Inline for showing assignments in course admin"""
    model = Assignment
    extra = 0
    fields = ['title', 'assignment_type', 'due_date', 'status', 'submission_count_display']
    readonly_fields = ['submission_count_display']
    
    def submission_count_display(self, obj):
        if obj.pk:
            return f"{obj.submission_count} submissions"
        return "No submissions yet"
    submission_count_display.short_description = 'Submissions'


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'assignment_type', 'due_date', 
        'status', 'submission_count_display', 'overdue_status'
    ]
    list_filter = [
        'assignment_type', 'status', 'due_date', 'created_at',
        'content_type', 'allow_late_submission'
    ]
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'submission_count_display', 'overdue_status']
    list_editable = ['status']
    list_per_page = 25
    date_hierarchy = 'due_date'
    
    
    def submission_count_display(self, obj):
        """Display submission count with link to submissions"""
        count = obj.submission_count
        if count > 0:
            url = reverse('admin:student_assignmentsubmission_changelist')
            return format_html(
                '<a href="{}?assignment__id__exact={}">{} submissions</a>',
                url, obj.id, count
            )
        return "0 submissions"
    submission_count_display.short_description = 'Submissions'
    
    def overdue_status(self, obj):
        """Display if assignment is overdue"""
        if obj.is_overdue:
            return format_html('<span style="color: red;">Overdue</span>')
        return format_html('<span style="color: green;">On time</span>')
    overdue_status.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('submissions')
    
    actions = ['mark_as_published', 'mark_as_archived']
    
    def mark_as_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(
            request,
            f'{updated} assignments marked as published.',
            messages.SUCCESS
        )
    mark_as_published.short_description = "Mark selected assignments as published"
    
    def mark_as_archived(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(
            request,
            f'{updated} assignments marked as archived.',
            messages.SUCCESS
        )
    mark_as_archived.short_description = "Mark selected assignments as archived"

@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', "status")
    search_fields = ('assignment', 'student', "status")


# Custom admin site configuration
admin.site.site_header = "Course Management System"
admin.site.site_title = "CMS Admin"
admin.site.index_title = "Welcome to Course Management System"


# ================================== CERTIFICATE MANAGEMENT ==================================

from import_export.admin import ImportExportModelAdmin
from .event_models import Event, Certificate, CertificateTemplate


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "start_date")
    search_fields = ("name", "code")


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    ordering = ("-created_at",)

class CertificateImportResource(resources.ModelResource):
    email = fields.Field(column_name="email")

    class Meta:
        model = Certificate
        import_id_fields = []  # We won't match existing certs by ID
        fields = ("email",)    # Only importing email column
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        email = row.get("email", "").strip().lower()
        if not email:
            raise Exception("Missing email field")

        try:
            student = Student.objects.get(email__iexact=email)
        except Student.DoesNotExist:
            # Skip row if student not found
            row["skip_reason"] = "Student not found"
            return

        event = Event.objects.latest("start_date")
        template_version = CertificateTemplate.objects.latest("created_at")

        # Create cert if it doesn't exist
        Certificate.objects.get_or_create(
            event=event,
            student=student,
            defaults={
                "approved": True,
                "template_version": template_version
            }
        )


@admin.register(Certificate)
class CertificateImportAdmin(ImportMixin, admin.ModelAdmin):
    resource_class = CertificateImportResource
    list_display = ("certificate_id", "student", "event", "approved", "issued_date")
    search_fields = ("certificate_id", "student__first_name", "student__last_name", "student__email")
    list_filter = ("approved", "event")
