from django.contrib import admin
from .models import Article, Comment

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