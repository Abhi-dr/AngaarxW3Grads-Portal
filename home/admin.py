from django.contrib import admin
from .models import Flames

# @admin.register(Flames)
# class FlamesAdmin(admin.ModelAdmin):
#     list_display = ('name', 'college', 'mode', 'created_at')
#     search_fields = ('name', 'whatsapp_number', 'contact_number', 'college', 'mode', 'created_at')
#     list_filter = ('name', 'whatsapp_number', 'contact_number', 'college', 'mode', 'created_at')
#     ordering = ('created_at',)
