from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.db import transaction as db_transaction
import logging

from .models import DepositRequest, WithdrawalRequest, Transaction
from account.models import User
from emails.email_utils import (
    send_deposit_approved_email, send_deposit_rejected_email, send_withdrawal_approved_email, send_withdrawal_rejected_email
)
from notification.services import (
    notify_deposit_approved, notify_deposit_rejected,notify_withdrawal_approved, notify_withdrawal_rejected
)

logger = logging.getLogger(__name__)

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
            # 🔔 Send notification + email
            notify_deposit_approved(deposit.user, deposit, admin_user=request.user)

            # 📧 Send approval email
            try:
                send_deposit_approved_email(deposit.user, deposit)
            except Exception as e:
                logger.error(f"Failed to send deposit approval email: {e}")
            
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
            # 🔔 Send notification + email
            notify_deposit_rejected(deposit.user, deposit, reason, admin_user=request.user)

            # 📧 Send rejection email
            try:
                send_deposit_rejected_email(deposit.user, deposit)
            except Exception as e:
                logger.error(f"Failed to send deposit rejection email: {e}")
            
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

             # 🔔 Send notification + email
            notify_withdrawal_approved(withdrawal.user, withdrawal, admin_user=request.user)
            

            # 📧 Send approval email
            try:
                send_withdrawal_approved_email(withdrawal.user, withdrawal)
            except Exception as e:
                logger.error(f"Failed to send withdrawal approval email: {e}")
            
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

            # 🔔 Send notification + email
            notify_withdrawal_rejected(withdrawal.user, withdrawal, reason, admin_user=request.user)

            # 📧 Send rejection email
            try:
                send_withdrawal_rejected_email(withdrawal.user, withdrawal)
            except Exception as e:
                logger.error(f"Failed to send withdrawal rejection email: {e}")
            
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


@login_required
@user_passes_test(admin_check)
def admin_transactions_list(request):
    """
    Display all transactions with filters.
    """
    transactions = Transaction.objects.select_related('user').all()
    
    # Apply filters
    type_filter = request.GET.get('type', 'all')
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('date', 'all')
    
    if type_filter != 'all':
        transactions = transactions.filter(transaction_type=type_filter)
    
    if status_filter != 'all':
        transactions = transactions.filter(status=status_filter)
    
    if search_query:
        transactions = transactions.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(reference__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if date_filter == 'today':
        transactions = transactions.filter(created_at__date=timezone.now().date())
    elif date_filter == 'week':
        transactions = transactions.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        )
    elif date_filter == 'month':
        transactions = transactions.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )
    
    # Stats
    total_transactions = Transaction.objects.count()
    total_volume = Transaction.objects.filter(
        status=Transaction.STATUS_COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    today_count = Transaction.objects.filter(
        created_at__date=timezone.now().date()
    ).count()
    
    transactions = transactions.order_by('-effective_date')
    
    context = {
        'transactions': transactions,
        'total_transactions': total_transactions,
        'total_volume': total_volume,
        'today_count': today_count,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'date_filter': date_filter,
    }
    
    return render(request, 'transaction/admin_transactions_list.html', context)


@login_required
@user_passes_test(admin_check)
def admin_transaction_detail(request, transaction_id):
    """Display transaction details."""
    transaction = get_object_or_404(
        Transaction.objects.select_related('user', 'related_deposit', 'related_withdrawal'),
        id=transaction_id
    )
    
    context = {
        'transaction': transaction,
    }
    
    return render(request, 'transaction/admin_transaction_detail.html', context)


@login_required
@user_passes_test(admin_check)
def admin_fund_management(request):
    """
    Admin tool to directly deposit/withdraw funds from any user account.
    Supports backdating for demo/testing purposes.
    """
    
    if request.method == 'POST':
        action = request.POST.get('action')  # 'deposit' or 'withdraw'
        user_id = request.POST.get('user_id')
        amount_str = request.POST.get('amount')
        txn_type = request.POST.get('transaction_type')
        description = request.POST.get('description', '').strip()
        effective_date_str = request.POST.get('effective_date', '').strip()
        
        # Validate user
        try:
            target_user = User.objects.get(id=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            messages.error(request, 'Please select a valid user.')
            return redirect('transaction:admin_fund_management')
        
        # Validate amount
        try:
            from decimal import Decimal, InvalidOperation
            amount = Decimal(amount_str)
            if amount <= 0:
                raise InvalidOperation("Amount must be greater than 0")
        except (InvalidOperation, ValueError, TypeError):
            messages.error(request, 'Please enter a valid amount.')
            return redirect('transaction:admin_fund_management')
        
        # Validate transaction type
        valid_types = [
            Transaction.TYPE_DEPOSIT,
            Transaction.TYPE_WITHDRAWAL,
            Transaction.TYPE_BONUS,
            Transaction.TYPE_FEE,
            Transaction.TYPE_BALANCE_ADJUSTMENT,
        ]
        if txn_type not in valid_types:
            messages.error(request, 'Please select a valid transaction type.')
            return redirect('transaction:admin_fund_management')
        
        # For withdrawals/fees, check balance
        if action == 'withdraw' and target_user.balance < amount:
            messages.error(
                request,
                f'Insufficient balance. {target_user.email} only has ${target_user.balance:.2f}.'
            )
            return redirect('transaction:admin_fund_management')
        
        # Parse effective date (for backdating)
        effective_date = None
        if effective_date_str:
            try:
                from datetime import datetime
                effective_date = datetime.strptime(effective_date_str, '%Y-%m-%dT%H:%M')
                # Make timezone-aware
                from django.utils import timezone
                if timezone.is_naive(effective_date):
                    effective_date = timezone.make_aware(effective_date)
            except ValueError:
                messages.error(request, 'Invalid date format.')
                return redirect('transaction:admin_fund_management')
        
        # Use database transaction for atomicity
        try:
            with db_transaction.atomic():
                # Calculate balance changes
                if action == 'deposit':
                    target_user.balance += amount
                    if txn_type == Transaction.TYPE_DEPOSIT:
                        target_user.total_deposited += amount
                elif action == 'withdraw':
                    target_user.balance -= amount
                    if txn_type == Transaction.TYPE_WITHDRAWAL:
                        target_user.total_withdrawn += amount
                
                target_user.save(update_fields=['balance', 'total_deposited', 'total_withdrawn', 'updated_at'])
                
                # Build description
                if not description:
                    if action == 'deposit':
                        description = f'Admin {txn_type} - credited to account'
                    else:
                        description = f'Admin {txn_type} - debited from account'
                
                # Create transaction record
                txn = Transaction.objects.create(
                    user=target_user,
                    transaction_type=txn_type,
                    amount=amount,
                    status=Transaction.STATUS_COMPLETED,
                    description=description,
                    balance_before=target_user.balance - amount if action == 'deposit' else target_user.balance + amount,
                    balance_after=target_user.balance,
                    effective_date=effective_date,
                    created_by_admin=request.user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                action_word = 'deposited' if action == 'deposit' else 'withdrew'
                date_note = f' (backdated to {effective_date.strftime("%b %d, %Y")})' if effective_date else ''
                
                messages.success(
                    request,
                    f'✅ Successfully {action_word} ${amount:.2f} {action_word[:-2]}ed '
                    f'{"to" if action == "deposit" else "from"} {target_user.email}. '
                    f'New balance: ${target_user.balance:.2f}{date_note}'
                )
                
                return redirect('transaction:admin_fund_management')
                
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            print(f"Admin fund management error: {e}")
            return redirect('transaction:admin_fund_management')
    
    # GET request: show the form
    # Get all users for the dropdown
    users = User.objects.all().order_by('email')
    
    # Get recent admin-created transactions
    recent_admin_txns = Transaction.objects.filter(
        created_by_admin__isnull=False
    ).select_related('user', 'created_by_admin').order_by('-effective_date')[:10]
    
    # Stats
    total_admin_txns = Transaction.objects.filter(created_by_admin__isnull=False).count()
    total_credited = Transaction.objects.filter(
        created_by_admin__isnull=False,
        transaction_type__in=[Transaction.TYPE_DEPOSIT, Transaction.TYPE_BONUS]
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_debited = Transaction.objects.filter(
        created_by_admin__isnull=False,
        transaction_type__in=[Transaction.TYPE_WITHDRAWAL, Transaction.TYPE_FEE]
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'users': users,
        'recent_admin_txns': recent_admin_txns,
        'total_admin_txns': total_admin_txns,
        'total_credited': total_credited,
        'total_debited': total_debited,
    }
    
    return render(request, 'transaction/admin_fund_management.html', context)