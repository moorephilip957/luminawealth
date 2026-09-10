from django.db import models
from django.conf import settings


class SupportTicket(models.Model):
    """
    Support ticket submitted by users.
    """
    
    # Status Choices
    STATUS_OPEN = 'open'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_WAITING_CUSTOMER = 'waiting_customer'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED = 'closed'
    
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_WAITING_CUSTOMER, 'Waiting for Customer'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]
    
    # Priority Choices
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'
    
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_URGENT, 'Urgent'),
    ]
    
    # Category Choices
    CATEGORY_GENERAL = 'general'
    CATEGORY_TECHNICAL = 'technical'
    CATEGORY_BILLING = 'billing'
    CATEGORY_ACCOUNT = 'account'
    CATEGORY_KYC = 'kyc'
    CATEGORY_DEPOSIT = 'deposit'
    CATEGORY_WITHDRAWAL = 'withdrawal'
    CATEGORY_STRATEGY = 'strategy'
    CATEGORY_OTHER = 'other'
    
    CATEGORY_CHOICES = [
        (CATEGORY_GENERAL, 'General Inquiry'),
        (CATEGORY_TECHNICAL, 'Technical Issue'),
        (CATEGORY_BILLING, 'Billing / Payments'),
        (CATEGORY_ACCOUNT, 'Account Issues'),
        (CATEGORY_KYC, 'KYC Verification'),
        (CATEGORY_DEPOSIT, 'Deposit Issues'),
        (CATEGORY_WITHDRAWAL, 'Withdrawal Issues'),
        (CATEGORY_STRATEGY, 'Investment Strategies'),
        (CATEGORY_OTHER, 'Other'),
    ]
    
    # Core Fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_tickets',
        help_text="User who submitted the ticket"
    )
    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Auto-generated ticket number"
    )
    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN
    )
    message = models.TextField(help_text="Initial message from user")
    
    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        help_text="Staff member assigned to this ticket"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['ticket_number']),
        ]
    
    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"
    
    def save(self, *args, **kwargs):
        # Auto-generate ticket number
        if not self.ticket_number:
            # Get the next ID
            if not self.pk:
                super().save(*args, **kwargs)
            self.ticket_number = f"SUP-{self.pk:06d}"
            kwargs['force_insert'] = False
        super().save(*args, **kwargs)
    
    @property
    def is_open(self):
        return self.status in [self.STATUS_OPEN, self.STATUS_IN_PROGRESS, self.STATUS_WAITING_CUSTOMER]
    
    @property
    def response_count(self):
        return self.responses.count()
    
    @property
    def last_response(self):
        return self.responses.order_by('-created_at').first()


class TicketResponse(models.Model):
    """
    Response to a support ticket (from user or staff).
    """
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="User or staff member who wrote this response"
    )
    is_staff_response = models.BooleanField(default=False)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Ticket Response'
        verbose_name_plural = 'Ticket Responses'
    
    def __str__(self):
        author_type = "Staff" if self.is_staff_response else "Customer"
        return f"{author_type} response on {self.ticket.ticket_number}"