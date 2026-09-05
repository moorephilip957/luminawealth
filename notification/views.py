from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from staff.decorators import client_login_required
from .models import Notification


@login_required
@client_login_required
def notifications_list(request):
    """
    Display all notifications for the current user.
    """
    user = request.user
    
    # Get filter parameters
    category_filter = request.GET.get('category', 'all')
    status_filter = request.GET.get('status', 'all')
    
    # Base queryset
    notifications = Notification.objects.filter(user=user)
    
    # Apply filters
    if category_filter != 'all':
        notifications = notifications.filter(category=category_filter)
    
    if status_filter == 'unread':
        notifications = notifications.filter(is_read=False)
    elif status_filter == 'read':
        notifications = notifications.filter(is_read=True)
    
    # Calculate stats
    total_notifications = Notification.objects.filter(user=user).count()
    unread_count = Notification.objects.filter(user=user, is_read=False).count()
    read_count = total_notifications - unread_count
    
    context = {
        'notifications': notifications,
        'total_notifications': total_notifications,
        'unread_count': unread_count,
        'read_count': read_count,
        'category_filter': category_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'notifications/notifications_list.html', context)


@login_required
@client_login_required
def notification_mark_read(request, notification_id):
    """Mark a single notification as read."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    # If there's a related URL, redirect to it
    if notification.related_url:
        return redirect(notification.related_url)
    
    # Otherwise, redirect back to notifications list
    return redirect('notification:notifications_list')


@login_required
@client_login_required
def notification_mark_all_read(request):
    """Mark all notifications as read for the current user."""
    if request.method == 'POST':
        unread_notifications = Notification.objects.filter(
            user=request.user, 
            is_read=False
        )
        count = unread_notifications.count()
        
        unread_notifications.update(
            is_read=True,
            read_at=timezone.now()
        )
        
        messages.success(request, f'✅ Marked {count} notification{"s" if count != 1 else ""} as read.')
    
    return redirect('notification:notifications_list')


@login_required
@client_login_required
def notification_delete(request, notification_id):
    """Delete a single notification."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    
    messages.success(request, 'Notification deleted.')
    return redirect('notification:notifications_list')


@login_required
@client_login_required
def notification_delete_all(request):
    """Delete all notifications for the current user."""
    if request.method == 'POST':
        count = Notification.objects.filter(user=request.user).count()
        Notification.objects.filter(user=request.user).delete()
        
        messages.success(request, f'🗑️ Deleted {count} notification{"s" if count != 1 else ""}.')
    
    return redirect('notification:notifications_list')


@login_required
@client_login_required
def notification_unread_count_api(request):
    """
    API endpoint to get unread notification count.
    Useful for AJAX polling to update the navbar badge.
    """
    count = Notification.get_unread_count(request.user)
    return JsonResponse({'unread_count': count})