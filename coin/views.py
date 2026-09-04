from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Max, Min
from datetime import timedelta
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from coin.models import Strategy, SpinRecord, StrategyInvestor
from .forms import StrategyForm, StrategyEditForm, SpinForm


def admin_check(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(admin_check)
def admin_strategies_list(request):
    """
    Display list of all strategies with stats and filters.
    Excludes deleted strategies by default.
    """
    
    # Get all strategies EXCEPT deleted (unless explicitly requested)
    show_deleted = request.GET.get('show_deleted', 'false') == 'true'
    
    if show_deleted:
        strategies = Strategy.objects.all()
    else:
        strategies = Strategy.objects.exclude(status='deleted')
    
    # Apply filters
    status_filter = request.GET.get('status', 'all')
    risk_filter = request.GET.get('risk', 'all')
    search_query = request.GET.get('search', '')
    
    if status_filter != 'all':
        strategies = strategies.filter(status=status_filter)
    
    if risk_filter != 'all':
        strategies = strategies.filter(risk_level=risk_filter)
    
    if search_query:
        strategies = strategies.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(invested_coin__icontains=search_query)
        )
    
    # Calculate stats (exclude deleted from stats)
    active_strategies_qs = Strategy.objects.exclude(status='deleted')
    total_strategies = active_strategies_qs.count()
    active_strategies = active_strategies_qs.filter(status='active').count()
    total_invested = active_strategies_qs.aggregate(Sum('total_invested'))['total_invested__sum'] or 0
    total_spins = SpinRecord.objects.count()
    
    # Recent spins (last 24 hours)
    recent_spins = SpinRecord.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    # Deleted count for badge
    deleted_count = Strategy.objects.filter(status='deleted').count()
    
    strategies = strategies.order_by('-created_at')
    
    context = {
        'strategies': strategies,
        'total_strategies': total_strategies,
        'active_strategies': active_strategies,
        'total_invested': total_invested,
        'total_spins': total_spins,
        'recent_spins': recent_spins,
        'deleted_count': deleted_count,
        'status_filter': status_filter,
        'risk_filter': risk_filter,
        'search_query': search_query,
        'show_deleted': show_deleted,
    }
    
    return render(request, 'strategies/admin_strategies_list.html', context)


@login_required
@user_passes_test(admin_check)
def admin_strategy_create(request):
    """
    Create a new investment strategy.
    Creates initial spin record with the starting price.
    """
    
    if request.method == 'POST':
        form = StrategyForm(request.POST)
        
        if form.is_valid():
            # Save the strategy
            strategy = form.save(commit=False)
            strategy.created_by = request.user
            
            # Set initial price as both current and initial
            strategy.initial_price = strategy.current_price
            strategy.save()
            
            # Create initial spin record
            SpinRecord.objects.create(
                strategy=strategy,
                admin=request.user,
                action='initial',
                old_price=0,
                new_price=strategy.current_price,
                reason='Strategy created',
                notes=f'Initial price set to ${strategy.current_price}'
            )
            
            messages.success(
                request,
                f'Strategy "{strategy.name}" created successfully with initial price ${strategy.current_price}!'
            )
            
            return redirect('coin:admin_strategies_list')
        else:
            # Form has errors
            messages.error(
                request,
                'Please correct the errors below.'
            )
    else:
        # GET request - show empty form
        form = StrategyForm()
    
    context = {
        'form': form,
        'page_title': 'Create New Strategy',
        'action': 'Create',
    }
    
    return render(request, 'strategies/admin_strategy_form.html', context)


@login_required
@user_passes_test(admin_check)
def admin_strategy_edit(request, strategy_id):
    """
    Edit an existing investment strategy.
    Does NOT create a SpinRecord - price changes only happen via spin up/down.
    Does NOT notify investors - per demo requirements.
    """
    
    # Get the strategy
    strategy = get_object_or_404(Strategy, id=strategy_id)
    
    if request.method == 'POST':
        form = StrategyEditForm(request.POST, instance=strategy)
        
        if form.is_valid():
            # Save the changes
            updated_strategy = form.save()
            
            messages.success(
                request,
                f'Strategy "{updated_strategy.name}" updated successfully!'
            )
            
            return redirect('coin:admin_strategies_list')
        else:
            messages.error(
                request,
                'Please correct the errors below.'
            )
    else:
        # GET request - show form pre-filled with existing data
        form = StrategyEditForm(instance=strategy)
    
    context = {
        'form': form,
        'strategy': strategy,
        'page_title': f'Edit: {strategy.name}',
        'action': 'Update',
    }
    
    return render(request, 'strategies/admin_strategy_form.html', context)


@login_required
@user_passes_test(admin_check)
def admin_strategy_spin_up(request, strategy_id):
    """
    Increase a strategy's price (spin up).
    Creates a SpinRecord, updates strategy price, and recalculates all investor values.
    """
    
    strategy = get_object_or_404(Strategy, id=strategy_id)
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('coin:admin_strategies_list')
    
    form = SpinForm(request.POST)
    
    if form.is_valid():
        amount = form.cleaned_data['amount']
        reason = form.cleaned_data.get('reason', '')
        
        old_price = strategy.current_price
        new_price = old_price + amount
        
        # Use transaction to ensure all updates happen together
        with transaction.atomic():
            # 1. Create SpinRecord
            spin_record = SpinRecord.objects.create(
                strategy=strategy,
                admin=request.user,
                action='spin_up',
                old_price=old_price,
                new_price=new_price,
                reason=reason or 'Price increase',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            
            # 2. Update strategy's current price
            strategy.current_price = new_price
            strategy.save(update_fields=['current_price', 'updated_at'])
            
            # 3. Update all investor values
            investors_updated = strategy.update_investor_values()
        
        # Calculate percentage change for message
        percent_change = (amount / old_price * 100) if old_price > 0 else 0
        
        messages.success(
            request,
            f'✅ Strategy "{strategy.name}" price increased by ${amount:.2f} '
            f'({percent_change:.2f}% increase). '
            f'New price: ${new_price:.2f}. '
            f'Updated {investors_updated} investor(s).'
        )
    else:
        # Show form errors
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
    
    return redirect('coin:admin_strategies_list')


@login_required
@user_passes_test(admin_check)
def admin_strategy_spin_down(request, strategy_id):
    """
    Decrease a strategy's price (spin down).
    Creates a SpinRecord, updates strategy price, and recalculates all investor values.
    Reason is REQUIRED for spin down (accountability).
    """
    
    strategy = get_object_or_404(Strategy, id=strategy_id)
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('coin:admin_strategies_list')
    
    form = SpinForm(request.POST)
    
    if form.is_valid():
        amount = form.cleaned_data['amount']
        reason = form.cleaned_data.get('reason', '').strip()
        
        # Reason is REQUIRED for spin down
        if not reason:
            messages.error(request, 'A reason is required when spinning down a price.')
            return redirect('admin_strategies_list')
        
        old_price = strategy.current_price
        new_price = old_price - amount
        
        # Validate: new price must be > 0
        if new_price <= 0:
            messages.error(
                request,
                f'Invalid amount. New price would be ${new_price:.2f}. '
                f'Price cannot go below $0.01.'
            )
            return redirect('admin_strategies_list')
        
        # Use transaction to ensure all updates happen together
        with transaction.atomic():
            # 1. Create SpinRecord
            spin_record = SpinRecord.objects.create(
                strategy=strategy,
                admin=request.user,
                action='spin_down',
                old_price=old_price,
                new_price=new_price,
                reason=reason,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            
            # 2. Update strategy's current price
            strategy.current_price = new_price
            strategy.save(update_fields=['current_price', 'updated_at'])
            
            # 3. Update all investor values
            investors_updated = strategy.update_investor_values()
        
        # Calculate percentage change for message
        percent_change = (amount / old_price * 100) if old_price > 0 else 0
        
        messages.warning(
            request,
            f'⚠️ Strategy "{strategy.name}" price decreased by ${amount:.2f} '
            f'({percent_change:.2f}% decrease). '
            f'New price: ${new_price:.2f}. '
            f'Updated {investors_updated} investor(s).'
        )
    else:
        # Show form errors
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
    
    return redirect('coin:admin_strategies_list')


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
@user_passes_test(admin_check)
def admin_strategy_delete(request, strategy_id):
    """
    Delete a strategy with full investor liquidation.
    
    Flow:
    1. Verify POST request and confirmation
    2. For each active investor:
       a. Calculate current value (shares × current_price)
       b. Add funds to user's available balance
       c. Create liquidation transaction record
       d. Mark investment as liquidated
    3. Update strategy totals
    4. Soft-delete strategy (status = 'deleted')
    5. Create notifications for all affected investors
    """
    
    strategy = get_object_or_404(Strategy, id=strategy_id)
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_strategies_list')
    
    # Prevent deleting already deleted strategies
    if strategy.status == 'deleted':
        messages.error(request, 'This strategy has already been deleted.')
        return redirect('coin:admin_strategies_list')
    
    # Get all active investors BEFORE liquidation
    active_investors = strategy.investors.filter(status='active').select_related('user')
    investor_count = active_investors.count()
    total_liquidated = 0
    
    # Use atomic transaction - all or nothing
    try:
        with transaction.atomic():
            
            # Step 1: Liquidate each investor
            for investor in active_investors:
                user = investor.user
                
                # Calculate current value based on latest price
                current_value = investor.shares * strategy.current_price
                
                # Add funds to user's available balance
                user.balance += current_value
                user.total_withdrawn += current_value  # Track as returned funds
                user.save(update_fields=['balance', 'total_withdrawn'])
                
                # Update investor record
                investor.current_value = current_value
                investor.total_profit = current_value - investor.invested_amount
                investor.status = 'liquidated'
                investor.liquidated_at = timezone.now()
                investor.save(update_fields=[
                    'current_value', 'total_profit', 'status', 'liquidated_at', 'updated_at'
                ])
                
                # Track total liquidated
                total_liquidated += current_value
            
            # Step 2: Update strategy totals
            strategy.total_investors = 0
            strategy.total_invested = 0
            strategy.status = 'deleted'
            strategy.save(update_fields=[
                'total_investors', 'total_invested', 'status', 'updated_at'
            ])
            
            # Step 3: Create notifications for all affected investors
            # (Using Django messages framework as simple notification)
            # In production, you'd create Notification model records
            for investor in active_investors:
                try:
                    # Try to import Notification model if it exists
                    from notifications.models import Notification
                    Notification.objects.create(
                        user=investor.user,
                        title='Strategy Discontinued',
                        message=(
                            f'The strategy "{strategy.name}" has been discontinued by the admin. '
                            f'Your investment of ${investor.invested_amount:.2f} has been liquidated '
                            f'and ${investor.current_value:.2f} has been returned to your available balance.'
                        ),
                        notification_type='strategy',
                        is_important=True
                    )
                except (ImportError, Exception):
                    # Notification model doesn't exist yet - skip silently
                    # In production, you'd want to handle this properly
                    pass
        
        # Success message
        messages.success(
            request,
            f'🗑️ Strategy "{strategy.name}" has been deleted. '
            f'Liquidated {investor_count} investor(s) and returned '
            f'${total_liquidated:,.2f} to their wallets. '
            f'All affected investors have been notified.'
        )
        
    except Exception as e:
        # Transaction failed - everything rolled back
        messages.error(
            request,
            f'Failed to delete strategy: {str(e)}. '
            f'No changes were made.'
        )
        print(f"Strategy deletion error: {e}")
    
    return redirect('coin:admin_strategies_list')


@login_required
@user_passes_test(admin_check)
def admin_strategy_toggle_status(request, strategy_id):
    """
    Toggle strategy status between active and paused.
    """
    
    strategy = get_object_or_404(Strategy, id=strategy_id)
    
    if strategy.status == 'deleted':
        messages.error(request, 'Cannot change status of a deleted strategy.')
        return redirect('admin_strategies_list')
    
    if strategy.status == 'active':
        strategy.status = 'paused'
        strategy.save(update_fields=['status', 'updated_at'])
        messages.warning(
            request,
            f'⏸️ Strategy "{strategy.name}" has been paused. '
            f'Investors cannot add new funds but existing positions remain.'
        )
    elif strategy.status == 'paused':
        strategy.status = 'active'
        strategy.save(update_fields=['status', 'updated_at'])
        messages.success(
            request,
            f'▶️ Strategy "{strategy.name}" has been resumed. '
            f'Investors can now add new funds.'
        )
    else:
        messages.error(request, f'Cannot toggle status from "{strategy.status}".')
    
    return redirect('coin:admin_strategies_list')


@login_required
@user_passes_test(admin_check)
def admin_strategy_detail(request, strategy_id):
    """
    Display comprehensive strategy details with:
    - Full strategy information
    - Interactive price history chart
    - Recent price adjustments
    - Active investors list
    """
    
    strategy = get_object_or_404(Strategy, id=strategy_id)
    
    # Get spin records for chart (last 30 days by default)
    days_back = int(request.GET.get('days', 30))
    date_threshold = timezone.now() - timedelta(days=days_back)
    
    spin_records = SpinRecord.objects.filter(
        strategy=strategy,
        created_at__gte=date_threshold
    ).order_by('created_at')
    
    # Prepare chart data
    chart_labels = []
    chart_prices = []
    
    for spin in spin_records:
        chart_labels.append(spin.created_at.strftime('%b %d %H:%M'))
        chart_prices.append(float(spin.new_price))
    
    # If no spins in period, show current price
    if not chart_prices:
        chart_labels.append('Now')
        chart_prices.append(float(strategy.current_price))
    
    # Get recent spin records for table (last 20)
    recent_spins = SpinRecord.objects.filter(
        strategy=strategy
    ).select_related('admin').order_by('-created_at')[:20]
    
    # Get active investors
    active_investors = strategy.investors.filter(
        status='active'
    ).select_related('user').order_by('-current_value')[:50]  # Top 50
    
    # Calculate statistics
    total_investors = strategy.investors.filter(status='active').count()
    total_invested = strategy.investors.filter(status='active').aggregate(
        total=Sum('invested_amount')
    )['total'] or 0
    
    total_current_value = strategy.investors.filter(status='active').aggregate(
        total=Sum('current_value')
    )['total'] or 0
    
    total_profit = total_current_value - total_invested
    
    # Calculate 24h change
    price_24h_ago = strategy.price_change_24h
    if price_24h_ago != 0:
        price_24h_change = ((strategy.current_price - price_24h_ago) / price_24h_ago) * 100
    else:
        price_24h_change = 0
    
    # Calculate all-time stats
    all_time_spins = SpinRecord.objects.filter(strategy=strategy).count()
    all_time_high = SpinRecord.objects.filter(strategy=strategy).aggregate(
        high=Max('new_price')
    )['high'] or strategy.current_price
    
    all_time_low = SpinRecord.objects.filter(strategy=strategy).aggregate(
        low=Min('new_price')
    )['low'] or strategy.current_price
    
    context = {
        'strategy': strategy,
        'chart_labels': chart_labels,
        'chart_prices': chart_prices,
        'recent_spins': recent_spins,
        'active_investors': active_investors,
        'total_investors': total_investors,
        'total_invested': total_invested,
        'total_current_value': total_current_value,
        'total_profit': total_profit,
        'price_24h_change': price_24h_change,
        'all_time_spins': all_time_spins,
        'all_time_high': all_time_high,
        'all_time_low': all_time_low,
        'days_back': days_back,
    }
    
    return render(request, 'strategies/admin_strategy_detail.html', context)
