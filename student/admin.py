from django.contrib import admin
from .models import Notification, Anonymous_Message, Feedback, AIQuestion, CourseRegistration
from .hackathon_models import HackathonTeam, TeamMember, JoinRequest, TeamInvite


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
    
    fieldsets = (
        ('Course Assignment', {
            'fields': ('content_type', 'object_id', 'title', 'description')
        }),
        ('Assignment Details', {
            'fields': ('assignment_type', 'max_score', 'instructions')
        }),
        ('Due Date & Submission Settings', {
            'fields': ('due_date', 'allow_late_submission', 'late_penalty_per_day')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Statistics', {
            'fields': ('submission_count_display', 'overdue_status'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
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


# @admin.register(AssignmentSubmission)
# class AssignmentSubmissionAdmin(admin.ModelAdmin):
#     list_display = [
#         'assignment', 'get_student_name', 'status', 
#         'score_display', 'submitted_at', 'late_status', 'graded_status'
#     ]
#     list_filter = [
#         'status', 'submitted_at', 'graded_at',
#         ('assignment', admin.RelatedOnlyFieldListFilter),
#         ('student', admin.RelatedOnlyFieldListFilter)
#     ]
#     search_fields = [
#         'assignment__title', 'student__username', 
#         'student__first_name', 'student__last_name'
#     ]
#     readonly_fields = [
#         'submitted_at', 'graded_at', 'late_status', 'penalty_display',
#         'final_score_display', 'submission_preview'
#     ]
#     list_editable = ['status']
#     list_per_page = 25
#     date_hierarchy = 'submitted_at'
    

#     def get_assignment_title(self, obj):
#         """Display assignment title with link"""
#         url = reverse('admin:student_assignment_change', args=[obj.assignment.pk])
#         return format_html('<a href="{}">{}</a>', url, obj.assignment.title)
#     get_assignment_title.short_description = 'Assignment'
#     get_assignment_title.admin_order_field = 'assignment__title'
    
#     def get_student_name(self, obj):
#         """Display student name with link"""
#         student = obj.student
#         full_name = f"{student.first_name} {student.last_name}".strip()
#         display_name = full_name if full_name else student.username
        
#         # Assuming student is in accounts app
#         url = reverse('admin:accounts_student_change', args=[student.pk])
#         return format_html('<a href="{}">{}</a>', url, display_name)
#     get_student_name.short_description = 'Student'
#     get_student_name.admin_order_field = 'student__username'
    
#     def score_display(self, obj):
#         """Display score with max score"""
#         if obj.score is not None:
#             max_score = obj.assignment.max_score
#             percentage = (obj.score / max_score * 100) if max_score > 0 else 0
#             color = 'green' if percentage >= 70 else 'orange' if percentage >= 50 else 'red'
#             return format_html(
#                 '<span style="color: {};">{}/{} ({}%)</span>',
#                 color, obj.score, max_score, round(percentage, 1)
#             )
#         return "Not graded"
#     score_display.short_description = 'Score'
    
#     def late_status(self, obj):
#         """Display if submission is late"""
#         if obj.is_late:
#             days = obj.days_late
#             return format_html(
#                 '<span style="color: red;">Late by {} day{}</span>',
#                 days, 's' if days != 1 else ''
#             )
#         return format_html('<span style="color: green;">On time</span>')
#     late_status.short_description = 'Late Status'
    
#     def graded_status(self, obj):
#         """Display grading status"""
#         if obj.graded_at:
#             return format_html('<span style="color: green;">Graded</span>')
#         return format_html('<span style="color: orange;">Pending</span>')
#     graded_status.short_description = 'Graded'
    
#     def penalty_display(self, obj):
#         """Display penalty percentage"""
#         penalty = obj.penalty_applied
#         if penalty > 0:
#             return f"{penalty}% penalty applied"
#         return "No penalty"
#     penalty_display.short_description = 'Penalty'
    
#     def final_score_display(self, obj):
#         """Display final score after penalty"""
#         final_score = obj.final_score
#         if final_score is not None:
#             return f"{final_score}/{obj.assignment.max_score}"
#         return "Not calculated"
#     final_score_display.short_description = 'Final Score'
    
#     def submission_preview(self, obj):
#         """Preview submission content based on type"""
#         content = obj.get_submission_content()
#         if not content:
#             return "No content"
        
#         assignment_type = obj.assignment.assignment_type
        
#         if assignment_type == 'text':
#             preview = str(content)[:100]
#             return f"{preview}..." if len(str(content)) > 100 else preview
#         elif assignment_type == 'code':
#             preview = str(content)[:100]
#             return format_html('<pre>{}</pre>', f"{preview}..." if len(str(content)) > 100 else preview)
#         elif assignment_type == 'link':
#             return format_html('<a href="{}" target="_blank">{}</a>', content, content)
#         elif assignment_type == 'file':
#             if content:
#                 return format_html('<a href="{}" target="_blank">View File</a>', content.url)
#         elif assignment_type == 'image':
#             if content:
#                 return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />', content.url)
        
#         return "Content available"
#     submission_preview.short_description = 'Preview'
    
#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related(
#             'assignment', 'student', 'assignment__content_type'
#         )
    
#     actions = ['accept_submissions', 'reject_submissions', 'mark_needs_revision']
    
#     def accept_submissions(self, request, queryset):
#         updated = queryset.update(status='accepted', graded_at=timezone.now())
#         self.message_user(
#             request,
#             f'{updated} submissions accepted.',
#             messages.SUCCESS
#         )
#     accept_submissions.short_description = "Accept selected submissions"
    
#     def reject_submissions(self, request, queryset):
#         updated = queryset.update(status='rejected', graded_at=timezone.now())
#         self.message_user(
#             request,
#             f'{updated} submissions rejected.',
#             messages.SUCCESS
#         )
#     reject_submissions.short_description = "Reject selected submissions"
    
#     def mark_needs_revision(self, request, queryset):
#         updated = queryset.update(status='needs_revision')
#         self.message_user(
#             request,
#             f'{updated} submissions marked as needing revision.',
#             messages.SUCCESS
#         )
#     mark_needs_revision.short_description = "Mark as needs revision"

@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', "status")
    search_fields = ('assignment', 'student', "status")


# Custom admin site configuration
admin.site.site_header = "Course Management System"
admin.site.site_title = "CMS Admin"
admin.site.index_title = "Welcome to Course Management System"
