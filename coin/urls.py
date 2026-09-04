from django.urls import path
from . import views

app_name = 'coin'

urlpatterns = [
    path('admin/strategies/', views.admin_strategies_list, name='admin_strategies_list'),
    # We'll add more URLs as we build the views
]