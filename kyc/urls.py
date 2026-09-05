from django.urls import path
from . import views

app_name = 'kyc'

urlpatterns = [
    path('staff/kyc/', views.admin_kyc_list, name='admin_kyc_list'),
    path('staff/kyc/<int:submission_id>/', views.admin_kyc_detail, name='admin_kyc_detail'),
    path('staff/kyc/<int:submission_id>/approve/', views.admin_kyc_approve, name='admin_kyc_approve'),
    path('staff/kyc/<int:submission_id>/reject/', views.admin_kyc_reject, name='admin_kyc_reject'),
    path('staff/kyc/<int:submission_id>/resubmit/', views.admin_kyc_resubmit, name='admin_kyc_resubmit'),

]