from django.urls import path
from . import views

app_name = 'notification'

urlpatterns = [
    path('notifications/',views.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/',views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/',views.notification_mark_all_read, name='notification_mark_all_read'),
    path('notifications/<int:notification_id>/delete/',views.notification_delete, name='notification_delete'),
    path('notifications/delete-all/',views.notification_delete, name='notification_delete_all')
]