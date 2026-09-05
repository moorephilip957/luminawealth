from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('all-users/', views.all_users_view, name='admin_users'),
    path('<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),

    path('admin/users/<int:user_id>/suspend/', views.admin_user_suspend, name='admin_user_suspend'),
    path('admin/users/<int:user_id>/reactivate/', views.admin_user_reactivate, name='admin_user_reactivate'),

    path('deposits/', views.admin_deposits_view, name='admin_deposits'),
    path('deposits/<int:deposit_id>/approve/', views.admin_deposit_approve, name='admin_deposit_approve'),
    path('deposits/<int:deposit_id>/reject/', views.admin_deposit_reject, name='admin_deposit_reject'),

    path('withdrawals/', views.admin_withdrawals_view, name='admin_withdrawals'),
    path('withdrawals/<int:withdrawal_id>/approve/', views.admin_withdrawal_approve, name='admin_withdrawal_approve'),
    path('withdrawals/<int:withdrawal_id>/reject/', views.admin_withdrawal_reject, name='admin_withdrawal_reject'),

    path('kyc/', views.admin_kyc_view, name='admin_kyc'),
    path('kyc/<int:kyc_id>/approve/', views.admin_kyc_approve, name='admin_kyc_approve'),
    path('kyc/<int:kyc_id>/reject/', views.admin_kyc_reject, name='admin_kyc_reject'),

    path('transactions/', views.admin_transactions, name='admin_transactions'),
    path('settings/', views.admin_settings, name='admin_settings'),
    path('settings/save/', views.admin_settings_save, name='admin_settings_save'),

    path('users/<int:user_id>/balance/', views.admin_user_balance, name='admin_user_balance'),
    path('users/<int:user_id>/balance/update/', views.admin_user_balance_update, name='admin_user_balance_update'),
]