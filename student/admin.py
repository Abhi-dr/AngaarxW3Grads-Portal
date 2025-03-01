from django.contrib import admin
from .models import Notification, Anonymous_Message, Feedback, AIQuestion, Hackathon


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

@admin.register(Hackathon)
class HackathonAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "location", "registration_deadline", "prize_pool")
    search_fields = ("name", "location")  
    list_filter = ("location", "start_date")  
    ordering = ("start_date",)
