from django.contrib import admin
from .models import Notification, Anonymous_Message, Feedback, AIQuestion, CourseRegistration, CourseSheet
from .hackathon_models import HackathonTeam, TeamMember, JoinRequest, TeamInvite
from .event_models import Event, Certificate, CertificateTemplate

from django.contrib import admin
from import_export.admin import ImportMixin
from import_export import resources, fields
from import_export.results import RowResult
from accounts.models import CustomUser
from import_export.widgets import ForeignKeyWidget


# Custom admin site configuration
admin.site.site_header = "The Angaar Batch Admin"
admin.site.site_title = "The Angaar Batch Admin Portal"
admin.site.index_title = "Welcome to The Angaar Batch Admin Portal"


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


# ================================== CERTIFICATE MANAGEMENT ==================================
#
# Signatory        — photo + signature preview
# CertificateTemplate — with TemplateSignatoryInline (ordered signatories)
# Certificate      — approve action, clear cache action, preview link, import
#

from import_export.admin import ImportMixin, ImportExportModelAdmin
from .event_models import Event, Certificate, CertificateTemplate, Signatory, TemplateSignatory


# ── Signatory ────────────────────────────────────────────────────────────────

@admin.register(Signatory)
class SignatoryAdmin(admin.ModelAdmin):
    list_display  = ("name", "designation", "organization", "is_active", "signature_preview")
    list_filter   = ("is_active",)
    search_fields = ("name", "designation", "organization")
    list_editable = ("is_active",)
    readonly_fields = ("signature_preview",)

    def signature_preview(self, obj):
        if obj.signature_image:
            return format_html(
                '<img src="{}" style="height:50px; background:#222; padding:4px; border-radius:4px;" />',
                obj.signature_image.url,
            )
        return "—"
    signature_preview.short_description = "Signature Preview"


# ── TemplateSignatory Inline ─────────────────────────────────────────────────

class TemplateSignatoryInline(admin.TabularInline):
    model   = TemplateSignatory
    extra   = 1
    fields  = ("signatory", "order")
    ordering = ("order",)
    verbose_name        = "Signatory"
    verbose_name_plural = "Signatories (drag to reorder — lower order = left on certificate)"


# ── CertificateTemplate ───────────────────────────────────────────────────────

@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display  = ("name", "certificate_type", "html_layout", "show_qr", "created_at")
    list_filter   = ("certificate_type", "html_layout", "show_qr")
    search_fields = ("name",)
    ordering      = ("-created_at",)
    inlines       = [TemplateSignatoryInline]
    readonly_fields = ("slug", "created_at", "updated_at")

    fieldsets = (
        (None, {
            "fields": ("name", "slug", "certificate_type", "html_layout"),
        }),
        ("Branding", {
            "fields": ("org_name", "org_logo"),
        }),
        ("Certificate Body", {
            "fields": ("body_text",),
            "description": (
                "Supports placeholders: {student_name}, {event_name}, "
                "{issued_date}, {hours}, {batch_name}"
            ),
        }),
        ("Feature Flags", {
            "fields": ("show_qr", "show_hours", "show_batch", "hours"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


# ── Event ─────────────────────────────────────────────────────────────────────

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display  = ("name", "code", "start_date", "end_date", "certificate_template")
    search_fields = ("name", "code")
    list_filter   = ("start_date", "certificate_template")

    fieldsets = (
        (None, {
            "fields": ("name", "code", "description"),
        }),
        ("Dates", {
            "fields": ("start_date", "end_date"),
        }),
        ("Certificate Template", {
            "fields": ("certificate_template",),
            "description": "Select the template for certificates issued for this event.",
        }),
    )


# ── Certificate import resource ───────────────────────────────────────────────

class CertificateImportResource(resources.ModelResource):
    email = fields.Field(column_name="email")

    class Meta:
        model           = Certificate
        import_id_fields = []
        fields          = ("email",)
        skip_unchanged  = True
        report_skipped  = True

    def before_import_row(self, row, **kwargs):
        email = row.get("email", "").strip().lower()
        if not email:
            raise Exception("Missing email field")

        try:
            student = CustomUser.objects.get(email__iexact=email)
        except CustomUser.DoesNotExist:
            row["skip_reason"] = "Student not found"
            return

        event_code = row.get("event_code", "").strip()
        try:
            event = Event.objects.get(code=event_code)
        except Event.DoesNotExist:
            row["skip_reason"] = f"Event '{event_code}' not found"
            return

        Certificate.objects.get_or_create(
            event=event,
            student=student,
            defaults={"approved": True},
        )


# ── Certificate ───────────────────────────────────────────────────────────────

@admin.register(Certificate)
class CertificateAdmin(ImportMixin, admin.ModelAdmin):
    resource_class = CertificateImportResource

    list_display = (
        "certificate_id", "student", "event", "approved",
        "issued_date", "has_cached_pdf_display", "preview_link",
    )
    list_filter   = ("approved", "event")
    search_fields = (
        "certificate_id",
        "student__first_name", "student__last_name", "student__email",
    )
    list_editable = ("approved",)
    readonly_fields = (
        "certificate_id", "issued_date",
        "template_snapshot_display", "preview_link", "has_cached_pdf_display",
    )
    actions = ["action_approve", "action_clear_cache", "action_prewarm_cache"]

    fieldsets = (
        (None, {
            "fields": ("event", "student", "approved"),
        }),
        ("Generated Fields", {
            "fields": ("certificate_id", "issued_date"),
            "classes": ("collapse",),
        }),
        ("Cache & Preview", {
            "fields": ("has_cached_pdf_display", "preview_link"),
        }),
        ("Template Snapshot (frozen at first generation)", {
            "fields": ("template_snapshot_display",),
            "classes": ("collapse",),
            "description": (
                "This is the frozen template state used to generate the PDF. "
                "It is written at the time of the first PDF download."
            ),
        }),
    )

    # ── Display helpers ───────────────────────────────────────────────────

    def has_cached_pdf_display(self, obj):
        if obj.has_cached_pdf():
            return format_html('<span style="color:green; font-weight:bold;">✓ Cached</span>')
        return format_html('<span style="color:#aaa;">✗ Not cached</span>')
    has_cached_pdf_display.short_description = "PDF cached?"

    def preview_link(self, obj):
        if not obj.pk:
            return "—"
        url = f"/dashboard/event/{obj.pk}/certificate/view"
        return format_html('<a href="{}" target="_blank">👁 Preview</a>', url)
    preview_link.short_description = "Preview"

    def template_snapshot_display(self, obj):
        import json
        if not obj.template_snapshot:
            return "Not generated yet"
        pretty = json.dumps(obj.template_snapshot, indent=2, ensure_ascii=False)
        return format_html(
            '<pre style="font-size:11px; max-height:300px; overflow:auto;">{}</pre>',
            pretty,
        )
    template_snapshot_display.short_description = "Template Snapshot (JSON)"

    # ── Admin actions ─────────────────────────────────────────────────────

    def action_approve(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(
            request,
            f"{updated} certificate(s) approved.",
            messages.SUCCESS,
        )
    action_approve.short_description = "✅ Approve selected certificates"

    def action_clear_cache(self, request, queryset):
        count = 0
        for cert in queryset:
            cert.invalidate_pdf_cache()
            count += 1
        self.message_user(
            request,
            f"Cleared PDF cache for {count} certificate(s).",
            messages.SUCCESS,
        )
    action_clear_cache.short_description = "🗑 Clear PDF cache for selected certificates"

    def action_prewarm_cache(self, request, queryset):
        from .tasks import pre_warm_certificate_pdf
        count = 0
        for cert in queryset.filter(approved=True):
            pre_warm_certificate_pdf.delay(cert.pk)
            count += 1
        self.message_user(
            request,
            f"Queued PDF pre-generation for {count} certificate(s). "
            "Check Celery worker logs for progress.",
            messages.INFO,
        )
    action_prewarm_cache.short_description = "🔥 Pre-generate PDFs (Celery async)"

