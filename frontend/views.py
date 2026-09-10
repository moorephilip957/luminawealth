from django.shortcuts import render,get_object_or_404
from .decorators import redirect_authenticated_users
from coin.models import Strategy
from django.db.models import Sum, Avg

@redirect_authenticated_users
def home_view(request):
    return render(request, 'frontend/index.html')

@redirect_authenticated_users
def about_view(request):
    return render(request, 'frontend/about.html')

@redirect_authenticated_users
def features_view(request):
    return render(request, 'frontend/features.html')

@redirect_authenticated_users
def contact_view(request):
    return render(request, 'frontend/contact.html')

@redirect_authenticated_users
def faq_view(request):
    return render(request, 'frontend/faq.html')

@redirect_authenticated_users
def strategies_view(request):
    """
    Public strategies showcase page.
    Shows all active, public strategies to anonymous visitors.
    Authenticated users are redirected to their dashboard.
    """
    
    # Base queryset: only active, public strategies
    strategies = Strategy.objects.filter(status='active', is_public=True)
    
    # 1. Filter by risk level
    risk_filter = request.GET.get('risk', 'all')
    if risk_filter != 'all':
        strategies = strategies.filter(risk_level=risk_filter)
    
    # 2. Sorting
    sort_by = request.GET.get('sort', 'popular')
    if sort_by == 'roi':
        strategies = strategies.order_by('-ai_accuracy')
    elif sort_by == 'popular':
        strategies = strategies.order_by('-total_investors')
    elif sort_by == 'minimum':
        strategies = strategies.order_by('min_investment')
    else:
        strategies = strategies.order_by('-total_investors')
    
    # Stats for the hero section
    all_strategies = Strategy.objects.filter(status='active', is_public=True)
    total_strategies = all_strategies.count()
    total_investors = all_strategies.aggregate(total=Sum('total_investors'))['total'] or 0
    avg_ai_accuracy = all_strategies.aggregate(avg=Avg('ai_accuracy'))['avg'] or 0
    
    context = {
        'strategies': strategies,
        'total_strategies': total_strategies,
        'total_investors': total_investors,
        'avg_ai_accuracy': round(avg_ai_accuracy, 1) if avg_ai_accuracy else 0,
        'risk_filter': risk_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'frontend/strategies2.html', context)


@redirect_authenticated_users
def strategy_detail_public(request, strategy_id):
    """
    Public strategy detail page.
    Shows strategy info and prompts anonymous users to sign up.
    """
    strategy = get_object_or_404(
        Strategy, 
        id=strategy_id, 
        is_public=True, 
        status='active'
    )
    
    # Calculate ROI
    if strategy.initial_price > 0:
        all_time_roi = ((strategy.current_price - strategy.initial_price) / strategy.initial_price) * 100
    else:
        all_time_roi = 0
    
    context = {
        'strategy': strategy,
        'all_time_roi': all_time_roi,
    }
    
    return render(request, 'frontend/strategy_detail.html', context)

@redirect_authenticated_users
def terms_view(request):
    return render(request, 'frontend/terms.html')

@redirect_authenticated_users
def privacy_view(request):
    return render(request, 'frontend/privacy.html')
