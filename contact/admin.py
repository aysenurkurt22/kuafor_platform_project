from django.contrib import admin
from .models import ContactMessage, Report

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'sent_at', 'is_read')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'sent_at')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'reason', 'content_object', 'reported_at', 'is_reviewed')
    list_filter = ('is_reviewed', 'reason', 'reported_at')
    search_fields = ('reporter__username', 'details')
    readonly_fields = ('reporter', 'reason', 'details', 'reported_at', 'content_object')
    list_editable = ('is_reviewed',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('reporter').prefetch_related('content_object')
