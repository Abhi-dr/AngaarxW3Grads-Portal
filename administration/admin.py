from django.contrib import admin
from .models import Achievement, SiteSettings

@admin.register(Achievement)
class Achievement(admin.ModelAdmin):
    list_display = ("student", "title", "date")
    search_fields = ("student__username", "title")
    list_filter = ("date",)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('maintenance_mode',)
