from django.contrib import admin
from django import forms

from .models import Sheet, Question, TestCase, Submission, POD, Streak, Batch, EnrollmentRequest, DriverCode


# ==================================== SHEET ====================================

class QuestionInline(admin.TabularInline):
    model = Sheet.questions.through  # Use the Many-to-Many through table
    extra = 0
    verbose_name = "Question"
    verbose_name_plural = "Questions"

@admin.register(Sheet)
class SheetAdmin(admin.ModelAdmin):
    list_display = ['name', "is_enabled", "is_sequential"]
    search_fields = ['name']
    list_per_page = 10

    inlines = [QuestionInline]


# ==================================== QUESTION ====================================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty_level', 'position', "is_approved", "show_complete_driver_code"]
    search_fields = ['title', 'sheets__name']  # Use 'sheets__name' since it's now ManyToMany
    list_per_page = 30
    list_filter = ['difficulty_level']  # Use 'sheets' for filtering by associated sheets
    ordering = ['-id']
    list_editable = ['position', "show_complete_driver_code"]
    
# ==================================== DRIVER CODE ====================================

@admin.register(DriverCode)
class DriverCodeAdmin(admin.ModelAdmin):
    list_display = ['question', 'language_id']
    search_fields = ['question__title', 'language_id']
    list_per_page = 30
    list_filter = ['language_id']

# ==================================== TEST CASE ====================================

@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['question', "input_data", "expected_output"]
    search_fields = ['question__title']
    list_per_page = 30
    list_filter = ['question__title']

# ==================================== SUBMISSION ====================================

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'status', 'language', "submitted_at"]
    search_fields = ['user__username', 'question__title', 'status', 'language']
    list_per_page = 30
    list_filter = ['status', 'language', "question"]

# ==================================== POD ====================================

@admin.register(POD)
class PODAdmin(admin.ModelAdmin):
    list_display = ['question', 'date']
    search_fields = ['question']
    list_per_page = 30
    list_filter = ['date']

# ==================================== STREAK ====================================

@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_streak']
    search_fields = ['user__username']
    list_per_page = 30
    list_filter = ['current_streak']


# ==================================== ENROLLMENT REQUEST ====================================
    
@admin.register(EnrollmentRequest)
class EnrollmentRequestAdmin(admin.ModelAdmin):
    list_display = ['student', 'batch', 'status']
    search_fields = ['student__username', 'batch__name']
    list_per_page = 30
    list_filter = ['batch']
    

# ==================================== BATCH ====================================

# @admin.register(Batch)
# class BatchAdmin(admin.ModelAdmin):
#     list_display = ['name']
#     search_fields = ['name']
#     list_per_page = 30


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    
    list_display = ['name', 'description']
