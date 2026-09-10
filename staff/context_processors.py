from django.contrib.auth import get_user_model

User = get_user_model()

def admin_stats(request):
    """
    Add global admin dashboard statistics to the context.
    Only runs for authenticated staff members to save database queries for public users.
    """
    if request.user.is_authenticated and request.user.is_staff:
        return {
            'total_users_count': User.objects.count(),
            'active_users_count': User.objects.filter(is_active=True).count(),
            # You can easily add more stats here later, for example:
            # 'pending_deposits_count': DepositRequest.objects.filter(status='pending').count(),
            # 'pending_kyc_count': KYCSubmission.objects.filter(status='pending').count(),
        }
    return {}