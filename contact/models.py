from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False) # New field for spam filtering

    class Meta:
        ordering = ('-sent_at',)

    def __str__(self):
        return f'Message from {self.name} ({self.email}) - {self.subject[:50]}...'

class Report(models.Model):
    REASON_CHOICES = (
        ('spam', 'Spam veya yanıltıcı'),
        ('inappropriate', 'Uygunsuz içerik'),
        ('offensive', 'Saldırgan veya taciz edici'),
        ('scam', 'Dolandırıcılık veya sahtekarlık'),
        ('other', 'Diğer'),
    )
    
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_made')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.TextField(blank=True, null=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)
    
    # Generic Foreign Key for the reported object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ('-reported_at',)
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f'Report by {self.reporter.username} for {self.content_object}'
