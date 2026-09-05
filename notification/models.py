from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    Notification model for user alerts.
    Used for KYC status, deposits, withdrawals, etc.
    """
    
    # Notification Type Choices
    TYPE_INFO = 'info'
    TYPE_SUCCESS = 'success'
    TYPE_WARNING = 'warning'
    TYPE_ERROR = 'error'
    
    TYPE_CHOICES = [
        (TYPE_INFO, 'Information'),
        (TYPE_SUCCESS, 'Success'),
        (TYPE_WARNING, 'Warning'),
        (TYPE_ERROR, 'Error'),
    ]
    
    # Category Choices (for filtering)
    CATEGORY_KYC = 'kyc'
    CATEGORY_DEPOSIT = 'deposit'
    CATEGORY_WITHDRAWAL = 'withdrawal'
    CATEGORY_STRATEGY = 'strategy'
    CATEGORY_SECURITY = 'security'
    CATEGORY_SYSTEM = 'system'
    
    CATEGORY_CHOICES = [
        (CATEGORY_KYC, 'KYC Verification'),
        (CATEGORY_DEPOSIT, 'Deposits'),
        (CATEGORY_WITHDRAWAL, 'Withdrawals'),
        (CATEGORY_STRATEGY, 'Strategies'),
        (CATEGORY_SECURITY, 'Security'),
        (CATEGORY_SYSTEM, 'System'),
    ]
    
    # Core Fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who receives this notification"
    )
    title = models.CharField(
        max_length=200,
        help_text="Notification title"
    )
    message = models.TextField(
        help_text="Notification message body"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_INFO
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_SYSTEM
    )
    
    # Status
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the user has read this notification"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the notification was marked as read"
    )
    
    # Optional: Link to related object
    related_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="URL to navigate to when clicked"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'category']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        """Mark this notification as read"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
    
    @classmethod
    def create_notification(cls, user, title, message, notification_type='info', 
                           category='system', related_url=''):
        """Helper method to create a notification"""
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            category=category,
            related_url=related_url
        )
    
    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for a user"""
        return cls.objects.filter(user=user, is_read=False).count()