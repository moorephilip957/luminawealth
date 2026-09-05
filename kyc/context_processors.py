from .models import KYCSubmission


def pending_kyc_count(request):
    """
    Add pending KYC submission count to all admin templates.
    This allows showing a badge in the admin sidebar.
    """
    if request.user.is_authenticated and request.user.is_staff:
        pending_count = KYCSubmission.objects.filter(
            status__in=[KYCSubmission.STATUS_PENDING, KYCSubmission.STATUS_UNDER_REVIEW]
        ).count()
        
        return {
            'pending_kyc_count': pending_count,
        }
    
    return {}