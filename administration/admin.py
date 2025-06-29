from django.contrib import admin
from .models import Achievement

@admin.register(Achievement)
class Achievement(admin.ModelAdmin):
    list_display = ("student", "title", "date")
    search_fields = ("student__username", "title")
    list_filter = ("date",)
