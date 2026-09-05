from django.urls import path
from . import views

app_name = 'transaction'

urlpatterns = [
    # Deposit Management
    path('staff/deposits/', views.admin_deposits_list, name='admin_deposits_list'),
    path('staff/deposits/<int:deposit_id>/', views.admin_deposit_detail, name='admin_deposit_detail'),
    path('staff/deposits/<int:deposit_id>/approve/', views.admin_deposit_approve, name='admin_deposit_approve'),
    path('staff/deposits/<int:deposit_id>/reject/', views.admin_deposit_reject, name='admin_deposit_reject'),

    # Admin Withdrawal Management
    path('staff/withdrawals/', views.admin_withdrawals_list, name='admin_withdrawals_list'),
    path('staff/withdrawals/<int:withdrawal_id>/', views.admin_withdrawal_detail, name='admin_withdrawal_detail'),
    path('staff/withdrawals/<int:withdrawal_id>/approve/', views.admin_withdrawal_approve, name='admin_withdrawal_approve'),
    path('staff/withdrawals/<int:withdrawal_id>/reject/', views.admin_withdrawal_reject, name='admin_withdrawal_reject'),

     # Admin Transaction History
    path('staff/transactions/', views.admin_transactions_list, name='admin_transactions_list'),
    path('staff/transactions/<int:transaction_id>/', views.admin_transaction_detail, name='admin_transaction_detail'),



]