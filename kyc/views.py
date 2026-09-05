from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import KYCSubmission
import logging

from emails.email_utils import send_kyc_approved_email, send_kyc_rejected_email
from notification.services import notify_kyc_approved, notify_kyc_rejected

logger = logging.getLogger(__name__)


def admin_check(user):
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(admin_check)
def admin_kyc_list(request):
    """
    Display list of all KYC submissions with filters.
    """
    submissions = KYCSubmission.objects.select_related('user', 'reviewed_by').all()
    
    # Apply filters
    status_filter = request.GET.get('status', 'pending')
    doc_type_filter = request.GET.get('doc_type', 'all')
    search_query = request.GET.get('search', '')
    
    if status_filter != 'all':
        submissions = submissions.filter(status=status_filter)
    
    if doc_type_filter != 'all':
        submissions = submissions.filter(document_type=doc_type_filter)
    
    if search_query:
        submissions = submissions.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(document_number__icontains=search_query)
        )
    
    # Calculate stats
    pending_count = KYCSubmission.objects.filter(
        status__in=[KYCSubmission.STATUS_PENDING, KYCSubmission.STATUS_UNDER_REVIEW]
    ).count()
    
    approved_count = KYCSubmission.objects.filter(status=KYCSubmission.STATUS_APPROVED).count()
    rejected_count = KYCSubmission.objects.filter(status=KYCSubmission.STATUS_REJECTED).count()
    resubmission_count = KYCSubmission.objects.filter(status=KYCSubmission.STATUS_RESUBMISSION).count()
    
    # Today's reviews
    today_reviews = KYCSubmission.objects.filter(
        reviewed_at__date=timezone.now().date()
    ).count()
    
    submissions = submissions.order_by('-submitted_at')
    
    context = {
        'submissions': submissions,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'resubmission_count': resubmission_count,
        'today_reviews': today_reviews,
        'status_filter': status_filter,
        'doc_type_filter': doc_type_filter,
        'search_query': search_query,
    }
    
    return render(request, 'kyc/admin_kyc_list.html', context)


@login_required
@user_passes_test(admin_check)
def admin_kyc_detail(request, submission_id):
    """
    Display detailed KYC submission with document viewer.
    """
    submission = get_object_or_404(
        KYCSubmission.objects.select_related('user', 'reviewed_by'),
        id=submission_id
    )
    
    # Get user's submission history
    user_submissions = KYCSubmission.objects.filter(
        user=submission.user
    ).order_by('-submitted_at')
    
    context = {
        'submission': submission,
        'user_submissions': user_submissions,
    }
    
    return render(request, 'kyc/admin_kyc_detail.html', context)


@login_required
@user_passes_test(admin_check)
def admin_kyc_approve(request, submission_id):
    """Approve a KYC submission."""
    submission = get_object_or_404(KYCSubmission, id=submission_id)
    
    if not submission.is_pending:
        messages.error(request, f'This submission has already been processed.')
        return redirect('kyc:admin_kyc_detail', submission_id=submission.id)
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '').strip()
        
        try:
            submission.approve(admin_user=request.user, notes=notes)
            # 🔔 Send notification + email
            notify_kyc_approved(submission.user, admin_user=request.user)

            # 📧 Send approval email
            try:
                send_kyc_approved_email(submission.user)
            except Exception as e:
                logger.error(f"Failed to send KYC approval email: {e}")
            
            messages.success(
                request,
                f'✅ KYC for {submission.user.email} has been approved. '
                f'User can now make withdrawals.'
            )
            
            return redirect('kyc:admin_kyc_list')
            
        except Exception as e:
            messages.error(request, f'Failed to approve: {str(e)}')
    
    return redirect('kyc:admin_kyc_detail', submission_id=submission.id)


@login_required
@user_passes_test(admin_check)
def admin_kyc_reject(request, submission_id):
    submission = get_object_or_404(KYCSubmission, id=submission_id)
    
    if not submission.is_pending:
        messages.error(request, f'This submission has already been processed.')
        return redirect('kyc:admin_kyc_detail', submission_id=submission.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        if not reason:
            messages.error(request, 'A rejection reason is required.')
            return redirect('kyc:admin_kyc_detail', submission_id=submission.id)
        
        try:
            submission.reject(admin_user=request.user, reason=reason, notes=notes)
            
            # 🚨 NEW: Flag ALL steps as needing resubmission
            submission.id_needs_resubmit = True
            submission.address_needs_resubmit = True
            submission.selfie_needs_resubmit = True
            submission.save(update_fields=[
                'id_needs_resubmit', 'address_needs_resubmit', 'selfie_needs_resubmit'
            ])

            notify_kyc_rejected(submission.user, reason, admin_user=request.user)
            # 📧 Send rejection email
            try:
                send_kyc_rejected_email(submission.user, reason)
            except Exception as e:
                logger.error(f"Failed to send KYC rejection email: {e}")
            
            messages.warning(
                request,
                f'⚠️ KYC for {submission.user.email} has been rejected. '
                f'User has been notified.'
            )
            
            return redirect('kyc:admin_kyc_list')
            
        except Exception as e:
            messages.error(request, f'Failed to reject: {str(e)}')
    
    return redirect('kyc:admin_kyc_detail', submission_id=submission.id)


@login_required
@user_passes_test(admin_check)
def admin_kyc_resubmit(request, submission_id):
    submission = get_object_or_404(KYCSubmission, id=submission_id)
    
    if not submission.is_pending:
        messages.error(request, f'This submission has already been processed.')
        return redirect('kyc:admin_kyc_detail', submission_id=submission.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        if not reason:
            messages.error(request, 'A reason is required.')
            return redirect('kyc:admin_kyc_detail', submission_id=submission.id)
        
        try:
            submission.request_resubmission(
                admin_user=request.user, 
                reason=reason, 
                notes=notes
            )
            
            # 🚨 NEW: Flag ALL steps as needing resubmission
            submission.id_needs_resubmit = True
            submission.address_needs_resubmit = True
            submission.selfie_needs_resubmit = True
            submission.save(update_fields=[
                'id_needs_resubmit', 'address_needs_resubmit', 'selfie_needs_resubmit'
            ])
            
            messages.info(
                request,
                f'ℹ️ {submission.user.email} has been asked to resubmit KYC documents.'
            )
            
            return redirect('kyc:admin_kyc_list')
            
        except Exception as e:
            messages.error(request, f'Failed: {str(e)}')
    
    return redirect('kyc:admin_kyc_detail', submission_id=submission.id)

