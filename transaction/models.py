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
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically create a pending transaction on first save.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Only create transaction on first save (new deposit request)
        if is_new:
            self._create_pending_transaction()
    
    def _create_pending_transaction(self):
        """Create a pending transaction record for this deposit request."""
        from .models import Transaction  # Import here to avoid circular imports if needed
        
        Transaction.create_transaction(
            user=self.user,
            transaction_type=Transaction.TYPE_DEPOSIT,
            amount=self.amount,
            description=f'Deposit request via {self.get_payment_method_display()}',
            related_deposit=self,
            status=Transaction.STATUS_PENDING
        )
    
    def approve(self, admin_user, notes=''):
        """Approve the deposit and add funds to user's balance."""
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
        
        # ✅ Update the related transaction to COMPLETED
        self._update_transaction_status(
            new_status='completed',
            description_suffix=''
        )
    
    def reject(self, admin_user, reason, notes=''):
        """Reject the deposit."""
        if not self.is_pending:
            raise ValueError(f"Cannot reject deposit with status: {self.status}")
        
        self.status = self.STATUS_REJECTED
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.rejection_reason = reason
        self.admin_notes = notes
        self.save()
        
        # ✅ Update the related transaction to FAILED
        self._update_transaction_status(
            new_status='failed',
            description_suffix=f' | Rejected: {reason}'
        )
    
    def _update_transaction_status(self, new_status, description_suffix=''):
        """
        Update the related transaction record status and balance_after.
        Called when admin approves or rejects the deposit.
        """
        from .models import Transaction
        
        # Find the pending transaction for this deposit
        transaction = Transaction.objects.filter(
            related_deposit=self,
            status=Transaction.STATUS_PENDING
        ).first()
        
        if not transaction:
            # Fallback: if no pending transaction found, create one (shouldn't happen normally)
            print(f"Warning: No pending transaction found for deposit #{self.id}")
            return
        
        # Update transaction
        transaction.status = new_status
        transaction.balance_after = self.user.balance  # Current balance after approval
        
        if description_suffix:
            transaction.description += description_suffix
        
        transaction.save(update_fields=['status', 'balance_after', 'description', 'updated_at'])


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

        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self._create_pending_transaction()
    
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
    
    def _create_pending_transaction(self):
        """Create a pending transaction record for this withdrawal request."""
        from .models import Transaction
        
        Transaction.create_transaction(
            user=self.user,
            transaction_type=Transaction.TYPE_WITHDRAWAL,
            amount=self.amount,
            description=f'Withdrawal request via {self.get_payment_method_display()}',
            related_withdrawal=self,
            status=Transaction.STATUS_PENDING
        )
    
    def approve(self, admin_user, transaction_hash='', notes=''):
        """Approve the withdrawal and deduct funds from user's balance."""
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
        
        # ✅ Update the related transaction to COMPLETED
        self._update_transaction_status(
            new_status='completed',
            description_suffix=''
        )
    
    def reject(self, admin_user, reason, notes=''):
        """Reject the withdrawal (funds stay in user's balance)."""
        if not self.is_pending:
            raise ValueError(f"Cannot reject withdrawal with status: {self.status}")
        
        self.status = self.STATUS_REJECTED
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.rejection_reason = reason
        self.admin_notes = notes
        self.save()
        
        # ✅ Update the related transaction to FAILED
        self._update_transaction_status(
            new_status='failed',
            description_suffix=f' | Rejected: {reason}'
        )
    
    def _update_transaction_status(self, new_status, description_suffix=''):
        """Update the related transaction record status and balance_after."""
        from .models import Transaction
        
        transaction = Transaction.objects.filter(
            related_withdrawal=self,
            status=Transaction.STATUS_PENDING
        ).first()
        
        if not transaction:
            print(f"Warning: No pending transaction found for withdrawal #{self.id}")
            return
        
        transaction.status = new_status
        transaction.balance_after = self.user.balance
        
        if description_suffix:
            transaction.description += description_suffix
        
        transaction.save(update_fields=['status', 'balance_after', 'description', 'updated_at'])


class Transaction(models.Model):
    """
    Unified transaction history for all financial activities.
    Tracks deposits, withdrawals, investments, returns, fees, etc.
    """
    
    # Transaction Type Choices
    TYPE_DEPOSIT = 'deposit'
    TYPE_WITHDRAWAL = 'withdrawal'
    TYPE_INVESTMENT = 'investment'
    TYPE_STRATEGY_RETURN = 'strategy_return'
    TYPE_LIQUIDATION = 'liquidation'
    TYPE_FEE = 'fee'
    TYPE_BONUS = 'bonus'
    TYPE_BALANCE_ADJUSTMENT = 'balance_adjustment'
    
    TYPE_CHOICES = [
        (TYPE_DEPOSIT, 'Deposit'),
        (TYPE_WITHDRAWAL, 'Withdrawal'),
        (TYPE_INVESTMENT, 'Investment'),
        (TYPE_STRATEGY_RETURN, 'Strategy Return'),
        (TYPE_LIQUIDATION, 'Liquidation'),
        (TYPE_FEE, 'Fee'),
        (TYPE_BONUS, 'Bonus'),
        (TYPE_BALANCE_ADJUSTMENT, 'Balance Adjustment'),
    ]
    
    # Status Choices
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    # Core Fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text="User this transaction belongs to"
    )
    transaction_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        help_text="Type of transaction"
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Transaction amount"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_COMPLETED
    )
    
    # Reference & Description
    reference = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique transaction reference"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the transaction"
    )
    
    # Balance tracking
    balance_before = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="User's balance before this transaction"
    )
    balance_after = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="User's balance after this transaction"
    )
    
    # Related objects (optional)
    related_deposit = models.ForeignKey(
        'DepositRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    related_withdrawal = models.ForeignKey(
        'WithdrawalRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
            models.Index(fields=['reference']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} #{self.reference} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        # Auto-generate reference if not provided
        if not self.reference:
            import uuid
            prefix = self.transaction_type[:3].upper()
            self.reference = f"{prefix}-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
    
    @property
    def is_credit(self):
        """Transaction adds to balance"""
        return self.transaction_type in [
            self.TYPE_DEPOSIT,
            self.TYPE_STRATEGY_RETURN,
            self.TYPE_LIQUIDATION,
            self.TYPE_BONUS,
        ] or (self.transaction_type == self.TYPE_BALANCE_ADJUSTMENT and self.amount > 0)
    
    @property
    def is_debit(self):
        """Transaction deducts from balance"""
        return self.transaction_type in [
            self.TYPE_WITHDRAWAL,
            self.TYPE_INVESTMENT,
            self.TYPE_FEE,
        ] or (self.transaction_type == self.TYPE_BALANCE_ADJUSTMENT and self.amount < 0)
    
    @classmethod
    def create_transaction(cls, user, transaction_type, amount, description='', 
                        related_deposit=None, related_withdrawal=None, 
                        ip_address=None, status=None):
        """
        Helper method to create a transaction with automatic balance tracking.
        
        Args:
            status: If None, defaults to COMPLETED. Use PENDING for requests awaiting approval.
        """
        # Default to COMPLETED if not specified
        if status is None:
            status = cls.STATUS_COMPLETED
        
        balance_before = user.balance
        
        # Calculate balance_after based on status
        if status == cls.STATUS_PENDING:
            # Pending: no balance change yet
            balance_after = balance_before
        else:
            # Completed/other: apply the balance change
            if transaction_type in [cls.TYPE_DEPOSIT, cls.TYPE_STRATEGY_RETURN, 
                                cls.TYPE_LIQUIDATION, cls.TYPE_BONUS]:
                balance_after = balance_before + abs(amount)
            elif transaction_type in [cls.TYPE_WITHDRAWAL, cls.TYPE_INVESTMENT, cls.TYPE_FEE]:
                balance_after = balance_before - abs(amount)
            elif transaction_type == cls.TYPE_BALANCE_ADJUSTMENT:
                balance_after = balance_before + amount
            else:
                balance_after = balance_before
        
        transaction = cls.objects.create(
            user=user,
            transaction_type=transaction_type,
            amount=abs(amount),
            description=description,
            balance_before=balance_before,
            balance_after=balance_after,
            related_deposit=related_deposit,
            related_withdrawal=related_withdrawal,
            ip_address=ip_address,
            status=status
        )
        
        return transaction