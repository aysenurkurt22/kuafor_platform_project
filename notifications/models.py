from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('MESSAGE', 'New Message'),
        ('ORDER_UPDATE', 'Order Update'),
        ('JOB_ALERT', 'Job Alert'),
        ('MEMBERSHIP', 'Membership Update'),
        ('OTHER', 'Other'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='OTHER')
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    # For generic foreign key, if needed later
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    # object_id = models.PositiveIntegerField(null=True, blank=True)
    # content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ('-timestamp',)

    def __str__(self):
        return f'{self.user.username} - {self.message[:50]}...'