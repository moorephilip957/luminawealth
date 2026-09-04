from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('portfolio/', views.portfolio_view, name='portfolio'),
    path('strategies/', views.strategies_view, name='strategies'),
    path('strategy-details/', views.strategy_details, name='strategy_details'),

    path('deposit/', views.deposit_view, name='deposit'),
    path('deposit/submit/', views.deposit_submit, name='deposit_submit'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('withdraw/submit/', views.withdraw_submit, name='withdraw_submit'),

    path('profile/', views.profile_view, name='profile'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('profile/settings/update/', views.profile_settings_update, name='profile_settings_update'),
    path('profile/password/update/', views.profile_password_update, name='profile_password_update'),
    path('profile/notifications/update/', views.profile_notifications_update, name='profile_notifications_update'),

    path('kyc/', views.kyc_view, name='kyc'),
    path('kyc/address/submit/', views.kyc_address_submit, name='kyc_address_submit'),

    path('notifications/', views.notifications_view, name='notifications'),
    path('transactions/', views.transaction_history, name='transaction_history'),

    path('verify-email-prompt/', views.email_verification_prompt_view, name='email_verification_prompt'),
    path('kyc-status/', views.kyc_status_view, name='kyc_status'),
]