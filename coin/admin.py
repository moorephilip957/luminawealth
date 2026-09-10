from django.contrib import admin
from .models import Strategy, StrategyInvestor, SpinRecord


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    # Fields displayed in the list view
    list_display = [
        'name', 
        'invested_coin', 
        'risk_level', 
        'ai_accuracy',
        'min_investment',
        'total_investors',  # ✅ Now visible in list
        'status',
        'is_public',
        'created_at'
    ]
    
    # Fields that can be edited directly from the list view (without opening the detail page)
    list_editable = [
        'status', 
        'is_public',
        'total_investors',  # ✅ Editable directly from list!
    ]
    
    # Filters on the right sidebar
    list_filter = [
        'status', 
        'is_public', 
        'risk_level', 
        'invested_coin',
        'created_at'
    ]
    
    # Search fields
    search_fields = [
        'name', 
        'description',
        'invested_coin'
    ]
    
    # Fields shown in the detail/edit form
    fields = [
        'name',
        'description',
        'strategy_type',
        'invested_coin',
        'risk_level',
        'ai_accuracy',
        'min_investment',
        'total_investors',  # ✅ Now in the edit form
        'initial_price',
        'current_price',
        'management_fee',
        'min_holding_period',
        'status',
        'is_public',
    ]
    
    # Read-only fields (if you want some fields to be uneditable)
    readonly_fields = ['created_at', 'updated_at']
    
    # Ordering
    ordering = ['-created_at']
    
    # Custom actions
    actions = ['make_public', 'make_private', 'reset_investor_count']
    
    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} strategies made public.')
    make_public.short_description = "Make selected strategies public"
    
    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} strategies made private.')
    make_private.short_description = "Make selected strategies private"
    
    def reset_investor_count(self, request, queryset):
        """Reset investor count to match actual StrategyInvestor records"""
        from django.db.models import Count
        for strategy in queryset:
            actual_count = StrategyInvestor.objects.filter(
                strategy=strategy, 
                status='active'
            ).count()
            strategy.total_investors = actual_count
            strategy.save(update_fields=['total_investors'])
        self.message_user(request, f'Investor counts synced with actual data for {queryset.count()} strategies.')
    reset_investor_count.short_description = "Sync investor count with actual data"


@admin.register(StrategyInvestor)
class StrategyInvestorAdmin(admin.ModelAdmin):
    list_display = ['user', 'strategy', 'invested_amount', 'current_value', 'status', 'invested_at']
    list_filter = ['status', 'strategy']
    search_fields = ['user__email', 'user__username', 'strategy__name']
    readonly_fields = ['invested_at', 'liquidated_at', 'updated_at']


@admin.register(SpinRecord)
class SpinRecordAdmin(admin.ModelAdmin):
    list_display = ['strategy', 'old_price', 'new_price', 'created_at']
    list_filter = ['strategy']
    readonly_fields = ['created_at']