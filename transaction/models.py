from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from account.models import User

class DepositRequest(models.Model):
    """
    Tracks all deposit requests from users.
    Admin must approve/reject each deposit before funds are added.
    """
    
    # Status Choices
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]
    
    # Payment Method Choices
    METHOD_BTC = 'btc'
    METHOD_ETH = 'eth'
    METHOD_USDT = 'usdt'
    METHOD_BANK_WIRE = 'bank_wire'
    # METHOD_SEPA = 'sepa'
    # METHOD_CARD = 'card'
    
    METHOD_CHOICES = [
        (METHOD_BTC, 'Bitcoin (BTC)'),
        (METHOD_ETH, 'Ethereum (ETH)'),
        (METHOD_USDT, 'USDT (TRC20)'),
        (METHOD_BANK_WIRE, 'Bank Wire Transfer'),
        # (METHOD_SEPA, 'SEPA Transfer'),
        # (METHOD_CARD, 'Credit/Debit Card'),
    ]
    
    # Core Fields
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='deposit_requests',
        help_text="User making the deposit"
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Deposit amount in USD"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        help_text="Payment method used"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        help_text="Current status of the deposit"
    )
    
    # Payment Details
    transaction_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text="Transaction hash or reference number from payment provider"
    )
    # payment_proof = models.FileField(
    #     upload_to='deposit_proofs/%Y/%m/',
    #     blank=True,
    #     null=True,
    #     help_text="Screenshot or receipt of payment"
    # )
    # sender_details = models.TextField(
    #     blank=True,
    #     help_text="Additional details (wallet address, bank name, etc.)"
    # )
    
    # Admin Processing
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_deposits',
        help_text="Admin who processed this deposit"
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the deposit was processed"
    )
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes from admin"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (shown to user)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Deposit Request'
        verbose_name_plural = 'Deposit Requests'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Deposit #{self.id} - ${self.amount} by {self.user.email} ({self.status})"
    
    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING
    
    @property
    def is_processed(self):
        return self.status in [self.STATUS_APPROVED, self.STATUS_COMPLETED, self.STATUS_REJECTED]
    
    def approve(self, admin_user, notes=''):
        """Approve the deposit and add funds to user's balance"""
        if not self.is_pending:
            raise ValueError(f"Cannot approve deposit with status: {self.status}")
        
        # Update user's balance
        self.user.balance += self.amount
        self.user.total_deposited += self.amount
        self.user.save(update_fields=['balance', 'total_deposited', 'updated_at'])
        
        # Update deposit status
        self.status = self.STATUS_COMPLETED
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.admin_notes = notes
        self.save()
    
    def reject(self, admin_user, reason, notes=''):
        """Reject the deposit"""
        if not self.is_pending:
            raise ValueError(f"Cannot reject deposit with status: {self.status}")
        
        self.status = self.STATUS_REJECTED
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.rejection_reason = reason
        self.admin_notes = notes
        self.save()


class WithdrawalRequest(models.Model):
    """
    Tracks all withdrawal requests from users.
    Admin must approve/reject each withdrawal before funds are released.
    """
    
    # Status Choices
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_REJECTED = 'rejected'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_FAILED, 'Failed'),
    ]
    
    # Payment Method Choices
    METHOD_BTC = 'btc'
    METHOD_ETH = 'eth'
    METHOD_USDT = 'usdt'
    METHOD_BANK_WIRE = 'bank_wire'
    METHOD_SEPA = 'sepa'
    
    METHOD_CHOICES = [
        (METHOD_BTC, 'Bitcoin (BTC)'),
        (METHOD_ETH, 'Ethereum (ETH)'),
        (METHOD_USDT, 'USDT (TRC20)'),
        (METHOD_BANK_WIRE, 'Bank Wire Transfer'),
        (METHOD_SEPA, 'SEPA Transfer'),
    ]
    
    # Core Fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='withdrawal_requests',
        help_text="User requesting the withdrawal"
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Withdrawal amount in USD"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        help_text="Withdrawal method"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        help_text="Current status of the withdrawal"
    )
    
    # Destination Details
    destination_address = models.CharField(
        max_length=500,
        help_text="Destination wallet address or bank account details"
    )
    destination_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name on the destination account (for bank transfers)"
    )
    network = models.CharField(
        max_length=50,
        blank=True,
        help_text="Blockchain network (e.g., ERC20, TRC20, Bitcoin Mainnet)"
    )
    
    # Fees
    network_fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0.00,
        help_text="Network/processing fee deducted from withdrawal"
    )
    amount_after_fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Amount user receives after fees"
    )
    
    # Transaction Details
    transaction_hash = models.CharField(
        max_length=200,
        blank=True,
        help_text="Blockchain transaction hash or bank reference"
    )
    
    # Admin Processing
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_withdrawals',
        help_text="Admin who processed this withdrawal"
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the withdrawal was processed"
    )
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes from admin"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (shown to user)"
    )
    
    # Security
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address where withdrawal was requested"
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        help_text="Browser/device info when requested"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Withdrawal Request'
        verbose_name_plural = 'Withdrawal Requests'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Withdrawal #{self.id} - ${self.amount} by {self.user.email} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate amount after fee
        if self.amount and self.network_fee is not None:
            self.amount_after_fee = self.amount - self.network_fee
        super().save(*args, **kwargs)
    
    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING
    
    @property
    def is_processed(self):
        return self.status in [
            self.STATUS_APPROVED, 
            self.STATUS_PROCESSING, 
            self.STATUS_COMPLETED, 
            self.STATUS_REJECTED
        ]
    
    @property
    def can_approve(self):
        """Check if withdrawal can be approved (user has enough balance)"""
        return self.is_pending and self.user.balance >= self.amount
    
    def approve(self, admin_user, transaction_hash='', notes=''):
        """
        Approve the withdrawal and deduct funds from user's balance.
        """
        if not self.is_pending:
            raise ValueError(f"Cannot approve withdrawal with status: {self.status}")
        
        if self.user.balance < self.amount:
            raise ValueError(
                f"Insufficient balance. User has ${self.user.balance:.2f} "
                f"but withdrawal is for ${self.amount:.2f}"
            )
        
        # Deduct from user's balance
        self.user.balance -= self.amount
        self.user.total_withdrawn += self.amount
        self.user.save(update_fields=['balance', 'total_withdrawn', 'updated_at'])
        
        # Update withdrawal status
        self.status = self.STATUS_COMPLETED
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.transaction_hash = transaction_hash
        self.admin_notes = notes
        self.save()
    
    def reject(self, admin_user, reason, notes=''):
        """Reject the withdrawal (funds stay in user's balance)"""
        if not self.is_pending:
            raise ValueError(f"Cannot reject withdrawal with status: {self.status}")
        
        self.status = self.STATUS_REJECTED
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.rejection_reason = reason
        self.admin_notes = notes
        self.save()