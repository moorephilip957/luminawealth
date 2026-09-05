from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import DepositRequest, WithdrawalRequest


def admin_check(user):
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(admin_check)
def admin_deposits_list(request):
    """
    Display list of all deposit requests with stats and filters.
    """
    
    deposits = DepositRequest.objects.select_related('user', 'processed_by').all()
    
    # Apply filters
    status_filter = request.GET.get('status', 'all')
    method_filter = request.GET.get('method', 'all')
    search_query = request.GET.get('search', '')
    
    if status_filter != 'all':
        deposits = deposits.filter(status=status_filter)
    
    if method_filter != 'all':
        deposits = deposits.filter(payment_method=method_filter)
    
    if search_query:
        deposits = deposits.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(transaction_reference__icontains=search_query)
        )
    
    # Calculate stats
    pending_count = DepositRequest.objects.filter(status=DepositRequest.STATUS_PENDING).count()
    pending_total = DepositRequest.objects.filter(
        status=DepositRequest.STATUS_PENDING
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    approved_today = DepositRequest.objects.filter(
        status=DepositRequest.STATUS_COMPLETED,
        processed_at__date=timezone.now().date()
    ).count()
    
    total_deposited = DepositRequest.objects.filter(
        status__in=[DepositRequest.STATUS_APPROVED, DepositRequest.STATUS_COMPLETED]
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    rejected_count = DepositRequest.objects.filter(status=DepositRequest.STATUS_REJECTED).count()
    
    deposits = deposits.order_by('-created_at')
    
    context = {
        'deposits': deposits,
        'pending_count': pending_count,
        'pending_total': pending_total,
        'approved_today': approved_today,
        'total_deposited': total_deposited,
        'rejected_count': rejected_count,
        'status_filter': status_filter,
        'method_filter': method_filter,
        'search_query': search_query,
    }
    
    return render(request, 'transaction/admin_deposits_list.html', context)


@login_required
@user_passes_test(admin_check)
def admin_deposit_detail(request, deposit_id):
    """
    Display detailed information about a specific deposit.
    """
    deposit = get_object_or_404(
        DepositRequest.objects.select_related('user', 'processed_by'),
        id=deposit_id
    )
    
    context = {
        'deposit': deposit,
    }
    
    return render(request, 'transaction/admin_deposit_detail.html', context)


@login_required
@user_passes_test(admin_check)
def admin_deposit_approve(request, deposit_id):
    """
    Approve a deposit request and add funds to user's balance.
    """
    deposit = get_object_or_404(DepositRequest, id=deposit_id)
    
    if not deposit.is_pending:
        messages.error(request, f'This deposit has already been {deposit.get_status_display().lower()}.')
        return redirect('staff:admin_deposit_detail', deposit_id=deposit.id)
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '').strip()
        
        try:
            deposit.approve(admin_user=request.user, notes=notes)
            
            messages.success(
                request,
                f'✅ Deposit #{deposit.id} approved! '
                f'${deposit.amount:.2f} added to {deposit.user.email}\'s balance. '
                f'New balance: ${deposit.user.balance:.2f}'
            )
            
            return redirect('transaction:admin_deposits_list')
            
        except Exception as e:
            messages.error(request, f'Failed to approve deposit: {str(e)}')
            print(f"Deposit approval error: {e}")
    
    return redirect('transaction:admin_deposit_detail', deposit_id=deposit.id)


@login_required
@user_passes_test(admin_check)
def admin_deposit_reject(request, deposit_id):
    """
    Reject a deposit request.
    """
    deposit = get_object_or_404(DepositRequest, id=deposit_id)
    
    if not deposit.is_pending:
        messages.error(request, f'This deposit has already been {deposit.get_status_display().lower()}.')
        return redirect('transaction:admin_deposit_detail', deposit_id=deposit.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        if not reason:
            messages.error(request, 'A rejection reason is required.')
            return redirect('transaction:admin_deposit_detail', deposit_id=deposit.id)
        
        try:
            deposit.reject(admin_user=request.user, reason=reason, notes=notes)
            
            messages.warning(
                request,
                f'⚠️ Deposit #{deposit.id} rejected. '
                f'User {deposit.user.email} has been notified of the reason.'
            )
            
            return redirect('transaction:admin_deposits_list')
            
        except Exception as e:
            messages.error(request, f'Failed to reject deposit: {str(e)}')
            print(f"Deposit rejection error: {e}")
    
    return redirect('transaction:admin_deposit_detail', deposit_id=deposit.id)


@login_required
@user_passes_test(admin_check)
def admin_withdrawals_list(request):
    """
    Display list of all withdrawal requests with stats and filters.
    """
    
    withdrawals = WithdrawalRequest.objects.select_related('user', 'processed_by').all()
    
    # Apply filters
    status_filter = request.GET.get('status', 'all')
    method_filter = request.GET.get('method', 'all')
    search_query = request.GET.get('search', '')
    
    if status_filter != 'all':
        withdrawals = withdrawals.filter(status=status_filter)
    
    if method_filter != 'all':
        withdrawals = withdrawals.filter(payment_method=method_filter)
    
    if search_query:
        withdrawals = withdrawals.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(destination_address__icontains=search_query) |
            Q(transaction_hash__icontains=search_query)
        )
    
    # Calculate stats
    pending_count = WithdrawalRequest.objects.filter(
        status=WithdrawalRequest.STATUS_PENDING
    ).count()
    
    pending_total = WithdrawalRequest.objects.filter(
        status=WithdrawalRequest.STATUS_PENDING
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    completed_today = WithdrawalRequest.objects.filter(
        status=WithdrawalRequest.STATUS_COMPLETED,
        processed_at__date=timezone.now().date()
    ).count()
    
    completed_today_total = WithdrawalRequest.objects.filter(
        status=WithdrawalRequest.STATUS_COMPLETED,
        processed_at__date=timezone.now().date()
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_withdrawn = WithdrawalRequest.objects.filter(
        status=WithdrawalRequest.STATUS_COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    rejected_count = WithdrawalRequest.objects.filter(
        status=WithdrawalRequest.STATUS_REJECTED
    ).count()
    
    withdrawals = withdrawals.order_by('-created_at')
    
    context = {
        'withdrawals': withdrawals,
        'pending_count': pending_count,
        'pending_total': pending_total,
        'completed_today': completed_today,
        'completed_today_total': completed_today_total,
        'total_withdrawn': total_withdrawn,
        'rejected_count': rejected_count,
        'status_filter': status_filter,
        'method_filter': method_filter,
        'search_query': search_query,
    }
    
    return render(request, 'transaction/admin_withdrawals_list.html', context)


@login_required
@user_passes_test(admin_check)
def admin_withdrawal_detail(request, withdrawal_id):
    """
    Display detailed information about a specific withdrawal.
    """
    withdrawal = get_object_or_404(
        WithdrawalRequest.objects.select_related('user', 'processed_by'),
        id=withdrawal_id
    )
    
    context = {
        'withdrawal': withdrawal,
    }
    
    return render(request, 'transaction/admin_withdrawal_detail.html', context)


@login_required
@user_passes_test(admin_check)
def admin_withdrawal_approve(request, withdrawal_id):
    """
    Approve a withdrawal request and deduct funds from user's balance.
    """
    withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    
    if not withdrawal.is_pending:
        messages.error(
            request, 
            f'This withdrawal has already been {withdrawal.get_status_display().lower()}.'
        )
        return redirect('transaction:admin_withdrawal_detail', withdrawal_id=withdrawal.id)
    
    if request.method == 'POST':
        transaction_hash = request.POST.get('transaction_hash', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        try:
            withdrawal.approve(
                admin_user=request.user,
                transaction_hash=transaction_hash,
                notes=notes
            )
            
            messages.success(
                request,
                f'✅ Withdrawal #{withdrawal.id} approved! '
                f'${withdrawal.amount:.2f} deducted from {withdrawal.user.email}. '
                f'New balance: ${withdrawal.user.balance:.2f}'
            )
            
            return redirect('transaction:admin_withdrawals_list')
            
        except ValueError as e:
            messages.error(request, f'Cannot approve: {str(e)}')
        except Exception as e:
            messages.error(request, f'Failed to approve withdrawal: {str(e)}')
            print(f"Withdrawal approval error: {e}")
    
    return redirect('transaction:admin_withdrawal_detail', withdrawal_id=withdrawal.id)


@login_required
@user_passes_test(admin_check)
def admin_withdrawal_reject(request, withdrawal_id):
    """
    Reject a withdrawal request (funds remain in user's balance).
    """
    withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
    
    if not withdrawal.is_pending:
        messages.error(
            request, 
            f'This withdrawal has already been {withdrawal.get_status_display().lower()}.'
        )
        return redirect('transaction:admin_withdrawal_detail', withdrawal_id=withdrawal.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        if not reason:
            messages.error(request, 'A rejection reason is required.')
            return redirect('transaction:admin_withdrawal_detail', withdrawal_id=withdrawal.id)
        
        try:
            withdrawal.reject(
                admin_user=request.user,
                reason=reason,
                notes=notes
            )
            
            messages.warning(
                request,
                f'⚠️ Withdrawal #{withdrawal.id} rejected. '
                f'Funds remain in {withdrawal.user.email}\'s balance.'
            )
            
            return redirect('transaction:admin_withdrawals_list')
            
        except Exception as e:
            messages.error(request, f'Failed to reject withdrawal: {str(e)}')
            print(f"Withdrawal rejection error: {e}")
    
    return redirect('transaction:admin_withdrawal_detail', withdrawal_id=withdrawal.id)


