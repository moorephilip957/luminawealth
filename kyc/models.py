from django.db import models
from django.conf import settings
from django.utils import timezone


class KYCSubmission(models.Model):
    """
    Tracks KYC (Know Your Customer) document submissions.
    Users upload ID documents and selfies for identity verification.
    """
    
    # Document Type Choices
    DOC_PASSPORT = 'passport'
    DOC_NATIONAL_ID = 'national_id'
    DOC_DRIVERS_LICENSE = 'drivers_license'
    
    DOC_TYPE_CHOICES = [
        (DOC_PASSPORT, 'Passport'),
        (DOC_NATIONAL_ID, 'National ID Card'),
        (DOC_DRIVERS_LICENSE, "Driver's License"),
    ]
    
    # Status Choices
    STATUS_PENDING = 'pending'
    STATUS_UNDER_REVIEW = 'under_review'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_RESUBMISSION = 'resubmission_requested'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_RESUBMISSION, 'Resubmission Requested'),
    ]
    
    # Core Fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='kyc_submissions',
        help_text="User who submitted KYC"
    )
    
    # Personal Information (as submitted)
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    nationality = models.CharField(max_length=100)
    residential_address = models.TextField()
    
    # Document Details
    document_type = models.CharField(
        max_length=20,
        choices=DOC_TYPE_CHOICES,
        help_text="Type of ID document submitted"
    )
    document_number = models.CharField(
        max_length=100,
        help_text="ID/Passport number"
    )
    document_expiry = models.DateField(
        null=True,
        blank=True,
        help_text="Document expiry date"
    )
    
    # Uploaded Documents
    document_front = models.ImageField(
        upload_to='kyc/documents/%Y/%m/%d/',
        help_text="Front side of ID document"
    )
    document_back = models.ImageField(
        upload_to='kyc/documents/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Back side of ID document (if applicable)"
    )
    selfie = models.ImageField(
        upload_to='kyc/selfies/%Y/%m/%d/',
        help_text="Selfie photo for identity verification"
    )
    proof_of_address = models.FileField(
        upload_to='kyc/address/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Proof of address (utility bill, bank statement)"
    )
    # Add this field to the KYCSubmission model
    address_doc_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of address proof document (e.g., utility_bill, bank_statement)"
    )
    
    # Status & Review
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    
    # Admin Review
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_kyc',
        help_text="Admin who reviewed this submission"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (shown to user)"
    )
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes from reviewer"
    )
    
    # Tracking
    submission_number = models.IntegerField(default=1)
    resubmission_count = models.IntegerField(default=0)

    # NEW: Per-step resubmission tracking
    id_needs_resubmit = models.BooleanField(
        default=False,
        help_text="True if admin requested ID document resubmission"
    )
    address_needs_resubmit = models.BooleanField(
        default=False,
        help_text="True if admin requested address proof resubmission"
    )
    selfie_needs_resubmit = models.BooleanField(
        default=False,
        help_text="True if admin requested selfie resubmission"
    )
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'KYC Submission'
        verbose_name_plural = 'KYC Submissions'
        indexes = [
            models.Index(fields=['user', '-submitted_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"KYC #{self.id} - {self.user.email} ({self.status})"
    
    @property
    def is_pending(self):
        return self.status in [self.STATUS_PENDING, self.STATUS_UNDER_REVIEW]
    
    @property
    def is_latest(self):
        """Check if this is the user's most recent submission"""
        latest = KYCSubmission.objects.filter(user=self.user).order_by('-submitted_at').first()
        return latest and latest.id == self.id
    
    def approve(self, admin_user, notes=''):
        """Approve the KYC submission"""
        if not self.is_pending:
            raise ValueError(f"Cannot approve submission with status: {self.status}")
        
        # Update user's KYC status
        self.user.kyc_status = 'approved'
        self.user.kyc_verified_at = timezone.now()
        self.user.save(update_fields=['kyc_status', 'kyc_verified_at', 'updated_at'])
        
        # Update submission
        self.status = self.STATUS_APPROVED
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.admin_notes = notes
        self.save()
    
    def reject(self, admin_user, reason, notes=''):
        """Reject the KYC submission"""
        if not self.is_pending:
            raise ValueError(f"Cannot reject submission with status: {self.status}")
        
        # Update user's KYC status
        self.user.kyc_status = 'rejected'
        self.user.kyc_rejection_reason = reason
        self.user.save(update_fields=['kyc_status', 'kyc_rejection_reason', 'updated_at'])
        
        # Update submission
        self.status = self.STATUS_REJECTED
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.admin_notes = notes
        self.save()
    
    def request_resubmission(self, admin_user, reason, notes=''):
        """Request user to resubmit with corrections"""
        if not self.is_pending:
            raise ValueError(f"Cannot request resubmission with status: {self.status}")
        
        self.user.kyc_status = 'rejected'
        self.user.kyc_rejection_reason = reason
        self.user.save(update_fields=['kyc_status', 'kyc_rejection_reason', 'updated_at'])
        
        self.status = self.STATUS_RESUBMISSION
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.admin_notes = notes
        self.save()