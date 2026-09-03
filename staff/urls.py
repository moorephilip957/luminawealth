from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('all-users/', views.all_users_view, name='admin_users'),

    path('deposits/', views.admin_deposits_view, name='admin_deposits'),
    path('deposits/<int:deposit_id>/approve/', views.admin_deposit_approve, name='admin_deposit_approve'),
    path('deposits/<int:deposit_id>/reject/', views.admin_deposit_reject, name='admin_deposit_reject'),

    path('withdrawals/', views.admin_withdrawals_view, name='admin_withdrawals'),
    path('withdrawals/<int:withdrawal_id>/approve/', views.admin_withdrawal_approve, name='admin_withdrawal_approve'),
    path('withdrawals/<int:withdrawal_id>/reject/', views.admin_withdrawal_reject, name='admin_withdrawal_reject'),

    path('kyc/', views.admin_kyc_view, name='admin_kyc'),
    path('kyc/<int:kyc_id>/approve/', views.admin_kyc_approve, name='admin_kyc_approve'),
    path('kyc/<int:kyc_id>/reject/', views.admin_kyc_reject, name='admin_kyc_reject'),

    path('strategies/', views.admin_strategies_view, name='admin_strategies'),
    path('strategies/<int:strategy_id>/spin-up/', views.admin_strategy_spin_up, name='admin_strategy_spin_up'),
    path('strategies/<int:strategy_id>/spin-down/', views.admin_strategy_spin_down, name='admin_strategy_spin_down'),
    path('strategies/create/', views.admin_strategy_create, name='admin_strategy_create'),

    path('transactions/', views.admin_transactions, name='admin_transactions'),
    path('settings/', views.admin_settings, name='admin_settings'),
    path('settings/save/', views.admin_settings_save, name='admin_settings_save'),

    path('users/<int:user_id>/', views.admin_user_details, name='admin_user_details'),
    path('users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('users/<int:user_id>/update/', views.admin_user_update, name='admin_user_update'),
    path('users/<int:user_id>/balance/', views.admin_user_balance, name='admin_user_balance'),
    path('users/<int:user_id>/balance/update/', views.admin_user_balance_update, name='admin_user_balance_update'),
]