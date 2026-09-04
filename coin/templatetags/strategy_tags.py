from django import template

register = template.Library()

@register.filter
def get_risk_color(risk_level):
    """Get Bootstrap color class for risk level"""
    colors = {
        'very_low': 'success',
        'low': 'info',
        'medium': 'primary',
        'high': 'warning',
        'very_high': 'danger',
    }
    return colors.get(risk_level, 'secondary')

@register.filter
def get_coin_icon(coin):
    """Get Bootstrap icon for coin type"""
    icons = {
        'btc': 'currency-bitcoin',
        'eth': 'currency-euro',  # Using euro as ETH icon
        'usdt': 'cash-stack',
        'usdc': 'cash-stack',
        'multi': 'diagram-3',
        'custom': 'coin',
    }
    return icons.get(coin, 'coin')

@register.filter
def get_coin_badge_color(coin):
    """Get Bootstrap badge color for coin"""
    colors = {
        'btc': 'warning',
        'eth': 'primary',
        'usdt': 'success',
        'usdc': 'success',
        'multi': 'info',
        'custom': 'secondary',
    }
    return colors.get(coin, 'secondary')