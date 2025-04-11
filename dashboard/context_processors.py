from .models import Notification

def dashboard_notifications(request):
    """
    Context processor to add dashboard notifications to template context
    """
    if not request.user.is_authenticated:
        return {'dashboard_notifications': [], 'unread_notifications_count': 0}
        
    # Get all unread notifications for this user or global notifications
    notifications = Notification.objects.filter(
        is_read=False,
        user=request.user
    ) | Notification.objects.filter(
        is_read=False,
        is_global=True
    )
    
    # Limit to most recent 5 notifications
    notifications = notifications.order_by('-created_at')[:5]
    
    # Get total unread count
    unread_count = notifications.count()
    
    return {
        'dashboard_notifications': notifications,
        'unread_notifications_count': unread_count
    } 