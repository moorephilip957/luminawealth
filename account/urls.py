from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [   
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),

    path('otp/', views.otp_verify_view, name='otp_verify'),
    path('otp/resend/', views.resend_otp_view, name='resend_otp'),

    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),
    path('resend-verification/', views.resend_verification_view, name='resend_verification'),
]