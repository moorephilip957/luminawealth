# support/context_processors.py
from .models import SupportTicket

def open_tickets_count(request):
    if request.user.is_authenticated and request.user.is_staff:
        return {
            'open_tickets_count': SupportTicket.objects.filter(
                status__in=[SupportTicket.STATUS_OPEN, SupportTicket.STATUS_IN_PROGRESS]
            ).count(),
        }
    return {}