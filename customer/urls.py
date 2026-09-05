from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('portfolio/', views.portfolio_view, name='portfolio'),

    path('strategies/', views.strategies_view, name='strategies'),
    path('strategies/<int:strategy_id>/', views.strategy_detail_view, name='strategy_detail'),
    path('strategies/<int:strategy_id>/add-funds/', views.add_funds_to_strategy, name='add_funds_to_strategy'),
    path('strategies/<int:strategy_id>/liquidate/', views.strategy_liquidate_view, name='strategy_liquidate'),

    path('deposit/', views.deposit_view, name='deposit'),
    # path('deposit/submit/', views.deposit_submit, name='deposit_submit'),
    path('withdraw/', views.withdraw_view, name='withdraw'),

    path('profile/', views.profile_view, name='profile'),
    path('profile/settings/', views.profile_settings_view, name='profile_settings'),

    path('kyc/', views.kyc_view, name='kyc'),

    path('notifications/', views.notifications_view, name='notifications'),
    path('transactions/', views.transaction_history, name='transaction_history'),

    path('verify-email-prompt/', views.email_verification_prompt_view, name='email_verification_prompt'),
    path('kyc-status/', views.kyc_status_view, name='kyc_status'),

     path('account-suspended/', views.account_suspended_view, name='account_suspended'),
]