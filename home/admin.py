from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'content', 'created_at')
    list_filter = ('title', 'created_at')
    ordering = ('created_at',)