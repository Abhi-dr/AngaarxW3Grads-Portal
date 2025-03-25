from django.contrib import admin
from .models import Article, Comment, FlamesCourse, FlamesCourseTestimonial, FlamesRegistration

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'get_likes_count')
    search_fields = ('title', 'content', 'created_at')
    list_filter = ('title', 'created_at')
    ordering = ('created_at',)
    
    def get_likes_count(self, obj):
        return obj.total_likes()
    get_likes_count.short_description = 'Likes'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'user', 'content', 'created_at')
    search_fields = ('article__title', 'user__username', 'content')
    list_filter = ('created_at', 'article')
    ordering = ('-created_at',)

# ================== FLAMES ===================

class FlamesCourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'is_active', 'created_at')
    list_filter = ('is_active', 'instructor')
    search_fields = ('title', 'subtitle', 'description')
    prepopulated_fields = {'slug': ('title',)}

class FlamesCourseTestimonialAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'course', 'rating')
    list_filter = ('course', 'rating')

class FlamesRegistrationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'course', 'email', 'college', 'created_at')
    list_filter = ('course', 'year', 'created_at')
    search_fields = ('full_name', 'email', 'college')

admin.site.register(FlamesCourse, FlamesCourseAdmin)
admin.site.register(FlamesCourseTestimonial, FlamesCourseTestimonialAdmin)
admin.site.register(FlamesRegistration, FlamesRegistrationAdmin)