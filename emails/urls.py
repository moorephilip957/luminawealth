from django.urls import path
from . import views

app_name = 'emails'

urlpatterns = [
    path('preview/', views.email_preview_index, name='email_preview_index'),
    path('preview/<str:template_name>/', views.email_preview, name='email_preview'),
]