from django.contrib import admin
from .models import Strategy, SpinRecord, StrategyPerformance, StrategyInvestor


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'invested_coin', 'current_price', 'risk_level',
        'total_investors', 'status', 'is_featured', 'created_at'
    ]
    list_filter = ['status', 'risk_level', 'invested_coin', 'is_featured', 'is_public']
    search_fields = ['name', 'description', 'invested_coin']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'market_cap', 'total_investors']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'short_description')
        }),
        ('Strategy Details', {
            'fields': ('invested_coin', 'strategy_type', 'risk_level')
        }),
        ('Pricing & Investment', {
            'fields': ('current_price', 'initial_price', 'min_investment', 'management_fee')
        }),
        ('Performance', {
            'fields': ('ai_accuracy', 'min_holding_period')
        }),
        ('Statistics', {
            'fields': ('total_investors', 'total_invested', 'market_cap')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_featured', 'is_public')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SpinRecord)
class SpinRecordAdmin(admin.ModelAdmin):
    list_display = [
        'strategy', 'action', 'old_price', 'new_price',
        'amount_changed', 'admin', 'created_at'
    ]
    list_filter = ['action', 'strategy', 'created_at']
    search_fields = ['strategy__name', 'reason', 'notes', 'admin__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'amount_changed']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Spin Details', {
            'fields': ('strategy', 'action', 'admin')
        }),
        ('Price Information', {
            'fields': ('old_price', 'new_price', 'amount_changed')
        }),
        ('Details', {
            'fields': ('reason', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StrategyPerformance)
class StrategyPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'strategy', 'date', 'open_price', 'close_price',
        'daily_change', 'daily_change_percent', 'volume'
    ]
    list_filter = ['strategy', 'date']
    search_fields = ['strategy__name']
    ordering = ['-date']
    date_hierarchy = 'date'


@admin.register(StrategyInvestor)
class StrategyInvestorAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'strategy', 'invested_amount', 'current_value',
        'profit_loss_percent', 'status', 'invested_at'
    ]
    list_filter = ['status', 'strategy', 'invested_at']
    search_fields = ['user__username', 'user__email', 'strategy__name']
    ordering = ['-invested_at']
    readonly_fields = ['invested_at', 'updated_at']