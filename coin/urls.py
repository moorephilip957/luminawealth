from django.urls import path
from . import views

app_name = 'coin'

urlpatterns = [
    path('admin/strategies/', views.admin_strategies_list, name='admin_strategies_list'),
    path('admin/strategies/create/', views.admin_strategy_create, name='admin_strategy_create'),
    path('admin/strategies/<int:strategy_id>/edit/', views.admin_strategy_edit, name='admin_strategy_edit'),
    path('admin/strategies/<int:strategy_id>/detail/', views.admin_strategy_detail, name='admin_strategy_detail'),

    path('admin/strategies/<int:strategy_id>/spin-up/', views.admin_strategy_spin_up, name='admin_strategy_spin_up'),
    path('admin/strategies/<int:strategy_id>/spin-down/', views.admin_strategy_spin_down, name='admin_strategy_spin_down'),
    path('admin/strategies/<int:strategy_id>/delete/', views.admin_strategy_delete, name='admin_strategy_delete'),
    path('admin/strategies/<int:strategy_id>/toggle-status/', views.admin_strategy_toggle_status, name='admin_strategy_toggle_status'),
    # We'll add detail view next

]