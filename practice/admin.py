from django.contrib import admin
from django import forms
from django.contrib.contenttypes.admin import GenericTabularInline

# Import all your models, including the new QuestionImage
from .models import (
    Sheet, Question, TestCase, Submission, POD, Streak, Batch, 
    EnrollmentRequest, DriverCode, MCQQuestion, MCQSubmission, QuestionImage
)

# ==================================== IMAGES ====================================

class QuestionImageInline(GenericTabularInline):
    model = QuestionImage
    extra = 1
    fields = ('image', 'caption', 'order')


# ==================================== SHEET ====================================

class QuestionInline(admin.TabularInline):
    model = Sheet.questions.through
    extra = 0
    verbose_name = "Coding Question"
    verbose_name_plural = "Coding Questions"

class MCQQuestionInline(admin.TabularInline):
    model = MCQQuestion
    extra = 1
    fields = ('question_text', 'difficulty_level', 'is_approved')
    verbose_name = "MCQ Question"
    verbose_name_plural = "MCQ Questions"

@admin.register(Sheet)
class SheetAdmin(admin.ModelAdmin):
    list_display = ['name', 'sheet_type', "is_enabled", "is_sequential"]
    search_fields = ['name']
    list_per_page = 10
    list_filter = ['sheet_type', 'is_enabled']

    def get_inlines(self, request, obj=None):
        if obj and obj.sheet_type == 'MCQ':
            return [MCQQuestionInline]
        return [QuestionInline]


# ==================================== QUESTION (CODING) ====================================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty_level', 'position', "is_approved", "show_complete_driver_code"]
    search_fields = ['title', 'sheets__name']
    list_per_page = 30
    list_filter = ['difficulty_level']
    ordering = ['-id']
    list_editable = ['position', "show_complete_driver_code"]
    inlines = [QuestionImageInline]

# ==================================== MCQ QUESTION ====================================

@admin.register(MCQQuestion)
class MCQQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'sheet', 'difficulty_level', "is_approved"]
    search_fields = ['question_text', 'sheet__name']
    list_per_page = 30
    list_filter = ['difficulty_level', 'sheet']
    ordering = ['-id']
    list_editable = ["is_approved"]
    inlines = [QuestionImageInline]

# ==================================== MCQ SUBMISSION ====================================

@admin.register(MCQSubmission)
class MCQSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'question', 'is_correct', 'submitted_at']
    search_fields = ['student__user__username', 'question__question_text']
    list_per_page = 30
    list_filter = ['question', 'is_correct']
    ordering = ['-submitted_at']


# ==================================== OTHER MODELS ====================================

@admin.register(DriverCode)
class DriverCodeAdmin(admin.ModelAdmin):
    list_display = ['question', 'language_id']
    search_fields = ['question__title', 'language_id']
    list_per_page = 30
    list_filter = ['language_id']

@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['question', "input_data", "expected_output"]
    search_fields = ['question__title']
    list_per_page = 30
    list_filter = ['question__title']

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'status', 'language', "submitted_at"]
    search_fields = ['user__username', 'question__title', 'status', 'language']
    list_per_page = 30
    list_filter = ['status', 'language', "question"]

@admin.register(POD)
class PODAdmin(admin.ModelAdmin):
    list_display = ['question', 'date']
    search_fields = ['question']
    list_per_page = 30
    list_filter = ['date']

@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_streak']
    search_fields = ['user__username']
    list_per_page = 30
    list_filter = ['current_streak']

@admin.register(EnrollmentRequest)
class EnrollmentRequestAdmin(admin.ModelAdmin):
    list_display = ['student', 'batch', 'status']
    search_fields = ['student__user__username', 'batch__name']
    list_per_page = 30
    list_filter = ['batch']

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']