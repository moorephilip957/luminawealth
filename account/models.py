import secrets
import string
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.crypto import get_random_string
from datetime import timedelta


class User(AbstractUser):
    """
    Custom User Model for LuminaWealthAI
    Extends Django's AbstractUser to add platform-specific fields.
    """
    
    # KYC Status Choices
    KYC_NOT_STARTED = 'not_started'
    KYC_PENDING = 'pending'
    KYC_APPROVED = 'approved'
    KYC_REJECTED = 'rejected'
    
    KYC_STATUS_CHOICES = [
        (KYC_NOT_STARTED, 'Not Started'),
        (KYC_PENDING, 'Pending Review'),
        (KYC_APPROVED, 'Approved'),
        (KYC_REJECTED, 'Rejected'),
    ]
    
    # ===== EMAIL VERIFICATION FIELDS =====
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email has been verified"
    )
    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the email was verified"
    )
    email_verification_token = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="Token for email verification link"
    )
    email_verification_token_created_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # ===== KYC VERIFICATION FIELDS =====
    kyc_status = models.CharField(
        max_length=20,
        choices=KYC_STATUS_CHOICES,
        default=KYC_NOT_STARTED,
        help_text="Current KYC verification status"
    )
    kyc_submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When KYC documents were submitted"
    )
    kyc_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When KYC was approved"
    )
    kyc_rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for KYC rejection (if rejected)"
    )
    
    # ===== PROFILE FIELDS =====
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Phone number (optional)"
    )
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        help_text="User's profile picture"
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="User's timezone"
    )
    preferred_currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="User's preferred currency (e.g., USD, EUR, GBP)"
    )
    
    # ===== FINANCIAL FIELDS =====
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00,
        help_text="Available balance in user's preferred currency"
    )
    total_invested = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00,
        help_text="Total amount currently invested in strategies"
    )
    total_deposited = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00,
        help_text="Total amount deposited (lifetime)"
    )
    total_withdrawn = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00,
        help_text="Total amount withdrawn (lifetime)"
    )
    
    # ===== SECURITY & TRACKING =====
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of last login"
    )
    failed_login_attempts = models.IntegerField(
        default=0,
        help_text="Number of consecutive failed login attempts"
    )
    account_locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Account is locked until this time (after too many failed attempts)"
    )
    
    # ===== METADATA =====
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time user was active on the platform"
    )
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['kyc_status']),
            models.Index(fields=['email_verified']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.email})"
    
    # ===== HELPER METHODS =====
    
    def generate_email_verification_token(self):
        """Generate a secure token for email verification"""
        self.email_verification_token = secrets.token_urlsafe(48)
        self.email_verification_token_created_at = timezone.now()
        
        # Save ALL fields, not just the token fields
        self.save()
        
        return self.email_verification_token
    
    def verify_email(self):
        """Mark email as verified"""
        self.email_verified = True
        self.email_verified_at = timezone.now()
        self.email_verification_token = None
        self.email_verification_token_created_at = None
        self.save(update_fields=[
            'email_verified',
            'email_verified_at',
            'email_verification_token',
            'email_verification_token_created_at'
        ])
    
    def is_email_verification_token_valid(self):
        """Check if email verification token is still valid (24 hours)"""
        if not self.email_verification_token:
            return False
        if not self.email_verification_token_created_at:
            return False
        
        token_age = timezone.now() - self.email_verification_token_created_at
        return token_age < timedelta(hours=24)
    
    def submit_kyc(self):
        """Mark KYC as submitted (pending review)"""
        self.kyc_status = self.KYC_PENDING
        self.kyc_submitted_at = timezone.now()
        self.save(update_fields=['kyc_status', 'kyc_submitted_at'])
    
    def approve_kyc(self):
        """Approve KYC verification"""
        self.kyc_status = self.KYC_APPROVED
        self.kyc_verified_at = timezone.now()
        self.kyc_rejection_reason = ''
        self.save(update_fields=[
            'kyc_status',
            'kyc_verified_at',
            'kyc_rejection_reason'
        ])
    
    def reject_kyc(self, reason=''):
        """Reject KYC verification with a reason"""
        self.kyc_status = self.KYC_REJECTED
        self.kyc_rejection_reason = reason
        self.save(update_fields=['kyc_status', 'kyc_rejection_reason'])
    
    def can_deposit(self):
        """Check if user can make deposits (requires email verification)"""
        return self.email_verified and self.is_active
    
    def can_withdraw(self):
        """Check if user can make withdrawals (requires KYC approval)"""
        return (
            self.email_verified and
            self.kyc_status == self.KYC_APPROVED and
            self.is_active
        )
    
    def can_invest(self):
        """Check if user can invest (requires email verification)"""
        return self.email_verified and self.is_active
    
    def is_account_locked(self):
        """Check if account is currently locked due to failed login attempts"""
        if not self.account_locked_until:
            return False
        return timezone.now() < self.account_locked_until
    
    def record_failed_login(self):
        """Record a failed login attempt, lock account after 5 attempts"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.account_locked_until = timezone.now() + timedelta(minutes=15)
        self.save(update_fields=[
            'failed_login_attempts',
            'account_locked_until'
        ])
    
    def record_successful_login(self, ip_address=None):
        """Record a successful login, reset failed attempts counter"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.last_login = timezone.now()
        self.last_login_ip = ip_address
        self.last_activity_at = timezone.now()
        self.save(update_fields=[
            'failed_login_attempts',
            'account_locked_until',
            'last_login',
            'last_login_ip',
            'last_activity_at'
        ])


class OTP(models.Model):
    """
    One-Time Password Model
    Stores OTP codes sent to users for login verification.
    Codes expire after 10 minutes and can only be used once.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='otps',
        help_text="User this OTP belongs to"
    )
    code = models.CharField(
        max_length=6,
        help_text="6-digit OTP code"
    )
    expires_at = models.DateTimeField(
        help_text="When this OTP expires"
    )
    used = models.BooleanField(
        default=False,
        help_text="Whether this OTP has been used"
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this OTP was used"
    )
    
    # Security tracking
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address that requested this OTP"
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        help_text="Browser/device info"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['code', 'used']),
        ]
    
    def __str__(self):
        status = 'Used' if self.used else ('Expired' if self.is_expired() else 'Active')
        return f"OTP for {self.user.email} - {status}"
    
    @classmethod
    def generate_code(cls):
        """Generate a secure 6-digit OTP code"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    @classmethod
    def create_otp(cls, user, ip_address=None, user_agent=''):
        """Create a new OTP for a user (expires in 10 minutes)"""
        # Invalidate any existing unused OTPs for this user
        cls.objects.filter(user=user, used=False).update(used=True)
        
        # Create new OTP
        otp = cls.objects.create(
            user=user,
            code=cls.generate_code(),
            expires_at=timezone.now() + timedelta(minutes=10),
            ip_address=ip_address,
            user_agent=user_agent[:500]
        )
        return otp
    
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if OTP is still valid (not used and not expired)"""
        return not self.used and not self.is_expired()
    
    def verify(self, code):
        """
        Verify the provided code against this OTP.
        Returns True if valid, False otherwise.
        Marks the OTP as used if verification succeeds.
        """
        if self.used:
            return False
        if self.is_expired():
            return False
        if self.code != code:
            return False
        
        # Mark as used
        self.used = True
        self.used_at = timezone.now()
        self.save(update_fields=['used', 'used_at'])
        return True
    
    @classmethod
    def get_active_otp(cls, user):
        """Get the most recent active (unused, unexpired) OTP for a user"""
        return cls.objects.filter(
            user=user,
            used=False,
            expires_at__gt=timezone.now()
        ).order_by('-created_at').first()
    
    @classmethod
    def has_recent_otp(cls, user, minutes=1):
        """Check if user has received an OTP in the last X minutes (rate limiting)"""
        recent_time = timezone.now() - timedelta(minutes=minutes)
        return cls.objects.filter(
            user=user,
            created_at__gte=recent_time
        ).exists()


class TrustedDevice(models.Model):
    """
    Trusted Device Model
    Tracks devices that users have marked as trusted to skip OTP.
    Devices expire after 30 days and can be revoked by the user.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='trusted_devices',
        help_text="User who owns this device"
    )
    device_token = models.CharField(
        max_length=64,
        unique=True,
        help_text="Unique token stored in browser cookie"
    )
    device_name = models.CharField(
        max_length=200,
        help_text="Friendly name like 'Chrome on Windows'"
    )
    device_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Device type (desktop, mobile, tablet)"
    )
    browser = models.CharField(
        max_length=100,
        blank=True,
        help_text="Browser name and version"
    )
    os = models.CharField(
        max_length=100,
        blank=True,
        help_text="Operating system"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address when device was trusted"
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Geographic location (city, country)"
    )
    
    last_used_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time this device was used"
    )
    expires_at = models.DateTimeField(
        help_text="When this trusted device expires (30 days)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this device is still trusted (can be revoked)"
    )
    
    class Meta:
        verbose_name = 'Trusted Device'
        verbose_name_plural = 'Trusted Devices'
        ordering = ['-last_used_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_token']),
        ]
    
    def __str__(self):
        status = 'Active' if self.is_active else 'Revoked'
        return f"{self.device_name} - {self.user.email} ({status})"
    
    @classmethod
    def generate_device_token(cls):
        """Generate a secure unique device token"""
        return secrets.token_urlsafe(48)
    
    @classmethod
    def create_trusted_device(cls, user, device_name, ip_address=None, 
                              device_type='', browser='', os='', location=''):
        """Create a new trusted device (expires in 30 days)"""
        device = cls.objects.create(
            user=user,
            device_token=cls.generate_device_token(),
            device_name=device_name[:200],
            device_type=device_type[:100],
            browser=browser[:100],
            os=os[:100],
            ip_address=ip_address,
            location=location[:200],
            expires_at=timezone.now() + timedelta(days=30)
        )
        return device
    
    def is_expired(self):
        """Check if trusted device has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if trusted device is still valid (active and not expired)"""
        return self.is_active and not self.is_expired()
    
    def revoke(self):
        """Revoke this trusted device"""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    def extend_expiry(self, days=30):
        """Extend the expiry date (e.g., when user uses the device)"""
        self.expires_at = timezone.now() + timedelta(days=days)
        self.save(update_fields=['expires_at'])
    
    def update_last_used(self, ip_address=None):
        """Update last used timestamp and optionally IP"""
        self.last_used_at = timezone.now()
        update_fields = ['last_used_at']
        if ip_address:
            self.ip_address = ip_address
            update_fields.append('ip_address')
        self.save(update_fields=update_fields)
    
    @classmethod
    def get_device_by_token(cls, token):
        """Get a trusted device by its token"""
        try:
            return cls.objects.get(device_token=token, is_active=True)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def cleanup_expired(cls):
        """Remove all expired trusted devices"""
        expired = cls.objects.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        return count
    
    @classmethod
    def get_friendly_device_name(cls, user_agent_string):
        """
        Parse user agent string to create a friendly device name.
        Example: "Chrome on Windows - New York, USA"
        """
        # Simple parsing - in production, use a library like user_agents
        ua = user_agent_string.lower()
        
        # Detect browser
        browser = 'Unknown Browser'
        if 'chrome' in ua and 'edg' not in ua:
            browser = 'Chrome'
        elif 'firefox' in ua:
            browser = 'Firefox'
        elif 'safari' in ua and 'chrome' not in ua:
            browser = 'Safari'
        elif 'edg' in ua:
            browser = 'Edge'
        
        # Detect OS
        os = 'Unknown OS'
        if 'windows' in ua:
            os = 'Windows'
        elif 'mac' in ua:
            os = 'macOS'
        elif 'linux' in ua:
            os = 'Linux'
        elif 'android' in ua:
            os = 'Android'
        elif 'iphone' in ua or 'ipad' in ua:
            os = 'iOS'
        
        # Detect device type
        device_type = 'Desktop'
        if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
            device_type = 'Mobile'
        elif 'ipad' in ua or 'tablet' in ua:
            device_type = 'Tablet'
        
        return f"{browser} on {os}"