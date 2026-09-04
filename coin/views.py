from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from coin.models import Strategy, SpinRecord, StrategyInvestor


def admin_check(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and user.is_staff


# @login_required
# @user_passes_test(admin_check)
def admin_strategies_list(request):
    """
    Display list of all strategies with stats and filters.
    """
    
    # Get all strategies
    strategies = Strategy.objects.all()
    
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
    
    # Calculate stats
    total_strategies = Strategy.objects.count()
    active_strategies = Strategy.objects.filter(status='active').count()
    total_invested = Strategy.objects.aggregate(Sum('total_invested'))['total_invested__sum'] or 0
    total_spins = SpinRecord.objects.count()
    
    # Recent spins (last 24 hours)
    recent_spins = SpinRecord.objects.filter(
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    # Order by most recent
    strategies = strategies.order_by('-created_at')
    
    context = {
        'strategies': strategies,
        'total_strategies': total_strategies,
        'active_strategies': active_strategies,
        'total_invested': total_invested,
        'total_spins': total_spins,
        'recent_spins': recent_spins,
        'status_filter': status_filter,
        'risk_filter': risk_filter,
        'search_query': search_query,
    }
    
    return render(request, 'strategies/admin_strategies_list.html', context)