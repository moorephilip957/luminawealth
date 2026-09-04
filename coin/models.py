from django.db import models
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone

from account.models import User


class Strategy(models.Model):
    """
    Investment Strategy Model
    Represents an AI-powered investment strategy that users can invest in.
    Each strategy has a current price that can be adjusted (spun up/down) by admins.
    """
    
    # Risk Level Choices
    RISK_CHOICES = [
        ('very_low', 'Very Low Risk'),
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('very_high', 'Very High Risk'),
    ]
    
    # Status Choices
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ]
    
    # Coin Choices (what the strategy is invested in)
    COIN_CHOICES = [
        ('btc', 'Bitcoin (BTC)'),
        ('eth', 'Ethereum (ETH)'),
        ('usdt', 'USDT'),
        ('usdc', 'USDC'),
        ('multi', 'Multi-Asset'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=200, blank=True)
    
    # Strategy Type & Coin
    invested_coin = models.CharField(max_length=20, choices=COIN_CHOICES, default='btc')
    strategy_type = models.CharField(max_length=50, default='DCA')  # e.g., DCA, Momentum, Yield Farming
    
    # Pricing & Investment
    current_price = models.DecimalField(max_digits=20, decimal_places=2, default=100.00)
    initial_price = models.DecimalField(max_digits=20, decimal_places=2, default=100.00)
    min_investment = models.DecimalField(max_digits=20, decimal_places=2, default=100.00)
    management_fee = models.DecimalField(max_digits=5, decimal_places=2, default=1.5)  # Annual fee percentage
    
    # Risk & Performance
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, default='medium')
    ai_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=94.7)  # Percentage
    min_holding_period = models.IntegerField(default=6)  # Months
    
    # Statistics
    total_investors = models.IntegerField(default=0)
    total_invested = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    
    # Status & Visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_strategies')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Strategy'
        verbose_name_plural = 'Strategies'
        indexes = [
            models.Index(fields=['status', 'is_public']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['-current_price']),
        ]
    
    def __str__(self):
        return f"{self.name} - ${self.current_price}"
    
    def get_absolute_url(self):
        return reverse('admin:strategy_detail', args=[self.id])
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from name if not provided
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        
        # Calculate market cap
        self.market_cap = self.current_price * self.total_investors
        
        super().save(*args, **kwargs)
    
    @property
    def price_change_24h(self):
        """Calculate 24-hour price change percentage"""
        recent_spins = self.spins.filter(
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        )
        
        if not recent_spins.exists():
            return Decimal('0.00')
        
        oldest_spin = recent_spins.order_by('created_at').first()
        old_price = oldest_spin.old_price
        
        if old_price == 0:
            return Decimal('0.00')
        
        change = ((self.current_price - old_price) / old_price) * 100
        return round(change, 2)
    
    @property
    def total_spins_count(self):
        """Get total number of price adjustments"""
        return self.spins.count()
    
    @property
    def risk_level_display_short(self):
        """Get short risk level display"""
        risk_map = {
            'very_low': 'Very Low',
            'low': 'Low',
            'medium': 'Medium',
            'high': 'High',
            'very_high': 'Very High',
        }
        return risk_map.get(self.risk_level, 'Medium')


class SpinRecord(models.Model):
    """
    Spin Record Model
    Tracks every price adjustment (spin up/down) made to a strategy.
    Used for generating price history charts and audit trails.
    """
    
    # Action Choices
    ACTION_CHOICES = [
        ('spin_up', 'Spin Up'),
        ('spin_down', 'Spin Down'),
        ('manual_set', 'Manual Set'),
        ('initial', 'Initial Price'),
    ]
    
    # Relationships
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='spins')
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='spin_records')
    
    # Price Information
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    old_price = models.DecimalField(max_digits=20, decimal_places=2)
    new_price = models.DecimalField(max_digits=20, decimal_places=2)
    amount_changed = models.DecimalField(max_digits=20, decimal_places=2)
    
    # Details
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Spin Record'
        verbose_name_plural = 'Spin Records'
        indexes = [
            models.Index(fields=['strategy', '-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.strategy.name} - {self.get_action_display()} - ${self.amount_changed} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Calculate amount changed
        self.amount_changed = abs(self.new_price - self.old_price)
        
        # Update strategy's current price
        if self.action != 'initial':
            self.strategy.current_price = self.new_price
            self.strategy.save(update_fields=['current_price', 'updated_at'])
        
        super().save(*args, **kwargs)
    
    @property
    def percentage_change(self):
        """Calculate percentage change"""
        if self.old_price == 0:
            return Decimal('0.00')
        
        change = ((self.new_price - self.old_price) / self.old_price) * 100
        return round(change, 2)
    
    @property
    def is_spin_up(self):
        """Check if this is a spin up action"""
        return self.action == 'spin_up'
    
    @property
    def is_spin_down(self):
        """Check if this is a spin down action"""
        return self.action == 'spin_down'


class StrategyPerformance(models.Model):
    """
    Strategy Performance Model
    Stores daily performance snapshots for historical charts and analytics.
    """
    
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='performance_records')
    date = models.DateField()
    
    # Price Data
    open_price = models.DecimalField(max_digits=20, decimal_places=2)
    close_price = models.DecimalField(max_digits=20, decimal_places=2)
    high_price = models.DecimalField(max_digits=20, decimal_places=2)
    low_price = models.DecimalField(max_digits=20, decimal_places=2)
    
    # Volume & Activity
    volume = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    trades_count = models.IntegerField(default=0)
    
    # Performance Metrics
    daily_change = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    daily_change_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Strategy Performance'
        verbose_name_plural = 'Strategy Performance Records'
        unique_together = ['strategy', 'date']
        indexes = [
            models.Index(fields=['strategy', '-date']),
            models.Index(fields=['-date']),
        ]
    
    def __str__(self):
        return f"{self.strategy.name} - {self.date} - ${self.close_price}"
    
    def save(self, *args, **kwargs):
        # Calculate daily change
        self.daily_change = self.close_price - self.open_price
        
        if self.open_price > 0:
            self.daily_change_percent = (self.daily_change / self.open_price) * 100
        else:
            self.daily_change_percent = Decimal('0.00')
        
        super().save(*args, **kwargs)


class StrategyInvestor(models.Model):
    """
    Strategy Investor Model
    Tracks which users are invested in which strategies.
    """
    
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='investors')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='strategy_investments')
    
    # Investment Details
    invested_amount = models.DecimalField(max_digits=20, decimal_places=2)
    current_value = models.DecimalField(max_digits=20, decimal_places=2)
    shares = models.DecimalField(max_digits=20, decimal_places=8)  # Number of shares/units
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('liquidated', 'Liquidated'),
    ], default='active')
    
    # Dates
    invested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    liquidated_at = models.DateTimeField(null=True, blank=True)
    
    # Profit/Loss
    total_profit = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    
    class Meta:
        ordering = ['-invested_at']
        verbose_name = 'Strategy Investor'
        verbose_name_plural = 'Strategy Investors'
        unique_together = ['strategy', 'user']
        indexes = [
            models.Index(fields=['strategy', 'status']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.strategy.name} - ${self.invested_amount}"
    
    @property
    def profit_loss_percent(self):
        """Calculate profit/loss percentage"""
        if self.invested_amount == 0:
            return Decimal('0.00')
        
        profit_percent = ((self.current_value - self.invested_amount) / self.invested_amount) * 100
        return round(profit_percent, 2)
    
    @property
    def is_profitable(self):
        """Check if investment is profitable"""
        return self.current_value > self.invested_amount