from django.contrib import admin
from .models import Notification, Anonymous_Message, Feedback, AIQuestion
from .hackathon_models import HackathonTeam, TeamMember, JoinRequest


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