from .models import WithdrawalRequest, DepositRequest

def pending_counts(request):
    """Add pending counts to all admin templates"""
    if request.user.is_authenticated and request.user.is_staff:
        return {
            'pending_deposit_count': DepositRequest.objects.filter(status=DepositRequest.STATUS_PENDING).count(),
        }
    return {}


def pending_counts(request):
    """Add pending counts to all admin templates"""
    if request.user.is_authenticated and request.user.is_staff:
        return {
            'pending_withdrawal_count': WithdrawalRequest.objects.filter(
                status=WithdrawalRequest.STATUS_PENDING
            ).count(),
            'pending_deposit_count': DepositRequest.objects.filter(
                status=DepositRequest.STATUS_PENDING
            ).count(),
        }
    return {}