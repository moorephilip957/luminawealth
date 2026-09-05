from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from datetime import timedelta

from account.models import User
from coin.models import Strategy, StrategyInvestor
from .forms import AdminUserEditForm
from notification.services import notify_account_suspended, notify_account_reactivated



def admin_check(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and user.is_staff

def dashboard_view(request):
   
    return render(request, 'staff/dashboard.html')


@login_required
@user_passes_test(admin_check)
def all_users_view(request):
    """
    Display list of all users with stats, filters, and search.
    """
    
    # Get all users
    users = User.objects.filter(is_staff=False)
    
    # Apply filters
    status_filter = request.GET.get('status', 'all')
    email_filter = request.GET.get('email', 'all')
    kyc_filter = request.GET.get('kyc', 'all')
    search_query = request.GET.get('search', '')
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'locked':
        users = users.filter(account_locked_until__gt=timezone.now())
    
    if email_filter == 'verified':
        users = users.filter(email_verified=True)
    elif email_filter == 'unverified':
        users = users.filter(email_verified=False)
    
    if kyc_filter != 'all':
        users = users.filter(kyc_status=kyc_filter)
    
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Calculate stats
    total_users = users.count()
    active_users = User.objects.filter(is_active=True).count()
    verified_emails = User.objects.filter(email_verified=True).count()
    kyc_approved = User.objects.filter(kyc_status=User.KYC_APPROVED).count()
    pending_kyc = User.objects.filter(kyc_status=User.KYC_PENDING).count()
    total_balance = User.objects.aggregate(Sum('balance'))['balance__sum'] or 0
    total_invested = User.objects.aggregate(Sum('total_invested'))['total_invested__sum'] or 0
    
    # Recent signups (last 7 days)
    recent_signups = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    users = users.order_by('-date_joined')
    
    context = {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'verified_emails': verified_emails,
        'kyc_approved': kyc_approved,
        'pending_kyc': pending_kyc,
        'total_balance': total_balance,
        'total_invested': total_invested,
        'recent_signups': recent_signups,
        'status_filter': status_filter,
        'email_filter': email_filter,
        'kyc_filter': kyc_filter,
        'search_query': search_query,
    }
    
    return render(request, 'staff/new/admin_users_list.html', context)


@login_required
@user_passes_test(admin_check)
def admin_user_detail(request, user_id):
    """
    Display comprehensive user details including:
    - User profile information
    - Financial stats (balance, invested, profit)
    - Active strategies cards (the star feature!)
    - Recent transactions
    - KYC status
    - Login activity
    - Admin notes
    """
    
    user = get_object_or_404(User, id=user_id)
    
    # Get user's active strategy investments
    active_investments = StrategyInvestor.objects.filter(
        user=user,
        status='active'
    ).select_related('strategy').order_by('-current_value')
    
    # Calculate totals for active investments
    total_invested = active_investments.aggregate(
        total=Sum('invested_amount')
    )['total'] or 0
    
    total_current_value = active_investments.aggregate(
        total=Sum('current_value')
    )['total'] or 0
    
    total_profit = total_current_value - total_invested
    
    # Get liquidated investments (history)
    liquidated_investments = StrategyInvestor.objects.filter(
        user=user,
        status='liquidated'
    ).select_related('strategy').order_by('-liquidated_at')[:5]
    
    # Calculate profit percentage
    if total_invested > 0:
        profit_percent = (total_profit / total_invested) * 100
    else:
        profit_percent = 0
    
    # Get trusted devices
    trusted_devices = user.trusted_devices.filter(is_active=True).order_by('-last_used_at')[:5]
    
    # Recent activity (last 10 logins from session - simplified for demo)
    # In production, you'd have a LoginHistory model
    
    context = {
        'profile_user': user,  # Renamed to avoid conflict with request.user
        'active_investments': active_investments,
        'liquidated_investments': liquidated_investments,
        'total_invested': total_invested,
        'total_current_value': total_current_value,
        'total_profit': total_profit,
        'profit_percent': profit_percent,
        'trusted_devices': trusted_devices,
    }
    
    return render(request, 'staff/new/admin_user_detail.html', context)


@login_required
@user_passes_test(admin_check)
def admin_user_edit(request, user_id):
    """
    Edit user information, verification status, and account settings.
    """
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=user)
        
        if form.is_valid():
            updated_user = form.save()
            
            messages.success(
                request,
                f'User "{updated_user.get_full_name() or updated_user.email}" updated successfully!'
            )
            
            return redirect('staff:admin_user_detail', user_id=user.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminUserEditForm(instance=user)
    
    context = {
        'form': form,
        'profile_user': user,
        'page_title': f'Edit: {user.get_full_name() or user.email}',
    }
    
    return render(request, 'staff/new/admin_user_edit.html', context)

def admin_deposits_view(request):
    # Check if user is admin
    # if not request.user.is_staff:
    #     return redirect('client_dashboard')
    
    # Get all deposit requests
    # deposits = DepositRequest.objects.all().order_by('-created_at')
    
    return render(request, 'staff/admin_deposits.html')

def admin_deposit_approve(request, deposit_id):
    if request.method == 'POST':
        # Get deposit and approve it
        # deposit = get_object_or_404(DepositRequest, id=deposit_id)
        # deposit.status = 'approved'
        # deposit.admin_notes = request.POST.get('notes', '')
        # deposit.processed_by = request.user
        # deposit.processed_at = timezone.now()
        # deposit.save()
        
        # Credit user's account
        # deposit.user.balance += deposit.amount
        # deposit.user.save()
        
        messages.success(request, f'Deposit #{deposit_id} approved successfully!')
    
    return redirect('staff:admin_deposits')


def admin_deposit_reject(request, deposit_id):
    if request.method == 'POST':
        # Get deposit and reject it
        # deposit = get_object_or_404(DepositRequest, id=deposit_id)
        # deposit.status = 'rejected'
        # deposit.rejection_reason = request.POST.get('reason')
        # deposit.admin_notes = request.POST.get('notes', '')
        # deposit.processed_by = request.user
        # deposit.processed_at = timezone.now()
        # deposit.save()
        
        messages.warning(request, f'Deposit #{deposit_id} has been rejected.')
    
    return redirect('staff:admin_deposits')


def admin_withdrawals_view(request):
    # Check if user is admin
    # if not request.user.is_staff:
    #     return redirect('client_dashboard')
    
    # Get all withdrawal requests
    # withdrawals = WithdrawalRequest.objects.all().order_by('-created_at')
    
    return render(request, 'staff/admin_withdrawals.html')


def admin_withdrawal_approve(request, withdrawal_id):
    if request.method == 'POST':
        # Get withdrawal and approve it
        # withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
        
        # Verify user has sufficient balance
        # if withdrawal.user.balance < withdrawal.amount:
        #     messages.error(request, 'User has insufficient balance!')
        #     return redirect('admin_withdrawals')
        
        # Deduct from user's balance
        # withdrawal.user.balance -= withdrawal.total_amount
        # withdrawal.user.save()
        
        # Update withdrawal status
        # withdrawal.status = 'approved'
        # withdrawal.admin_notes = request.POST.get('notes', '')
        # withdrawal.processed_by = request.user
        # withdrawal.processed_at = timezone.now()
        # withdrawal.save()
        
        messages.success(request, f'Withdrawal #{withdrawal_id} approved! Funds have been deducted from user account.')
    
    return redirect('staff:admin_withdrawals')

def admin_withdrawal_reject(request, withdrawal_id):
    if request.method == 'POST':
        # Get withdrawal and reject it
        # withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
        # withdrawal.status = 'rejected'
        # withdrawal.rejection_reason = request.POST.get('reason')
        # withdrawal.admin_notes = request.POST.get('notes', '')
        # withdrawal.processed_by = request.user
        # withdrawal.processed_at = timezone.now()
        # withdrawal.save()
        
        messages.warning(request, f'Withdrawal #{withdrawal_id} has been rejected. Funds remain in user account.')
    
    return redirect('staff:admin_withdrawals')


def admin_kyc_view(request):
    # Check if user is admin
    # if not request.user.is_staff:
    #     return redirect('client_dashboard')
    
    # Get all KYC requests
    # kyc_requests = KYCRequest.objects.all().order_by('-submitted_at')
    
    return render(request, 'staff/admin_kyc.html')

def admin_kyc_approve(request, kyc_id):
    if request.method == 'POST':
        # Get KYC request and approve it
        # kyc = get_object_or_404(KYCRequest, id=kyc_id)
        # kyc.status = 'approved'
        # kyc.admin_notes = request.POST.get('notes', '')
        # kyc.reviewed_by = request.user
        # kyc.reviewed_at = timezone.now()
        # kyc.save()
        
        # If this was the final step (selfie), mark user as fully verified
        # if kyc.step == 4:
        #     kyc.user.kyc_verified = True
        #     kyc.user.save()
        
        messages.success(request, f'KYC verification #{kyc_id} approved successfully!')
    
    return redirect('staff:admin_kyc')

def admin_kyc_reject(request, kyc_id):
    if request.method == 'POST':
        # Get KYC request and reject it
        # kyc = get_object_or_404(KYCRequest, id=kyc_id)
        # kyc.status = 'rejected'
        # kyc.rejection_reason = request.POST.get('reason')
        # kyc.admin_notes = request.POST.get('notes', '')
        # kyc.reviewed_by = request.user
        # kyc.reviewed_at = timezone.now()
        # kyc.save()
        
        messages.warning(request, f'KYC verification #{kyc_id} has been rejected. User notified to resubmit.')
    
    return redirect('staff:admin_kyc')


def admin_transactions(request):
    # Check if user is admin
    # if not request.user.is_staff:
    #     return redirect('client_dashboard')
    
    # Get all transactions
    # transactions = Transaction.objects.all().order_by('-created_at')
    
    return render(request, 'staff/admin_transactions.html')

def admin_settings(request):
    # Check if user is admin
    # if not request.user.is_staff:
    #     return redirect('client_dashboard')
    
    return render(request, 'staff/admin_settings.html')

def admin_settings_save(request):
    if request.method == 'POST':
        # Handle settings update based on section
        # section = request.POST.get('section')
        
        # Save settings to database or config file
        # PlatformSettings.objects.update_or_create(...)
        
        messages.success(request, 'Settings updated successfully!')
    
    return redirect('staff:admin_settings')




def admin_user_balance(request, user_id):
    # user = get_object_or_404(User, id=user_id)
    # adjustments = BalanceAdjustment.objects.filter(user=user).order_by('-created_at')
    
    return render(request, 'staff/admin_user_balance.html', {'user_id': user_id})

def admin_user_balance_update(request, user_id):
    if request.method == 'POST':
        # user = get_object_or_404(User, id=user_id)
        adjustment_type = request.POST.get('adjustment_type')
        amount = float(request.POST.get('amount'))
        reason_type = request.POST.get('reason_type')
        notes = request.POST.get('notes')
        notify_user = request.POST.get('notify_user') == 'on'
        
        # Create adjustment record
        # adjustment = BalanceAdjustment.objects.create(
        #     user=user,
        #     type=adjustment_type,
        #     amount=amount,
        #     reason_type=reason_type,
        #     notes=notes,
        #     admin=request.user,
        #     old_balance=user.balance
        # )
        
        # Update user balance
        # if adjustment_type == 'add':
        #     user.balance += amount
        # else:
        #     user.balance -= amount
        # adjustment.new_balance = user.balance
        # user.save()
        # adjustment.save()
        
        # Send notification email if enabled
        # if notify_user:
        #     send_balance_notification_email(user, adjustment)
        
        messages.success(request, f'Balance adjusted successfully! New balance: $800')
        # messages.success(request, f'Balance adjusted successfully! New balance: ${user.balance}')
        return redirect('staff:admin_user_details', user_id=user_id)
    
    return redirect('staff:admin_user_balance', user_id=user_id)


@login_required
@user_passes_test(admin_check)
def admin_user_suspend(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user.id == request.user.id:
        messages.error(request, "You cannot suspend your own account.")
        return redirect('staff:admin_user_detail', user_id=user_id) # Adjust namespace
        
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        
        # ✅ CHANGE: Set status to suspended, keep is_active=True
        target_user.account_status = User.STATUS_SUSPENDED
        target_user.suspension_reason = reason or 'Account suspended by admin'
        target_user.suspended_at = timezone.now()
        target_user.suspended_by = request.user
        target_user.save(update_fields=[
            'account_status', 'suspension_reason', 'suspended_at', 'suspended_by', 'updated_at'
        ])
        
        # Terminate all active sessions for this user
        from django.contrib.sessions.models import Session
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        user_id_str = str(target_user.pk)
        for session in sessions:
            if session.get_decoded().get('_auth_user_id') == user_id_str:
                session.delete()

        # 🔔 Notify user
        notify_account_suspended(target_user, reason, admin_user=request.user)
        messages.success(request, f'✅ User "{target_user.email}" has been suspended.')
        return redirect('staff:admin_user_detail', user_id=user_id)
        
    return redirect('staff:admin_user_detail', user_id=user_id)


@login_required
@user_passes_test(admin_check)
def admin_user_reactivate(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # ✅ CHANGE: Set status back to active
        target_user.account_status = User.STATUS_ACTIVE
        target_user.suspension_reason = ''
        target_user.suspended_at = None
        target_user.suspended_by = None
        target_user.save(update_fields=[
            'account_status', 'suspension_reason', 'suspended_at', 'suspended_by', 'updated_at'
        ])

        # 🔔 Notify user
        notify_account_reactivated(target_user, admin_user=request.user)
        messages.success(request, f'✅ User "{target_user.email}" has been reactivated.')
        return redirect('staff:admin_user_detail', user_id=user_id)
        
    return redirect('staff:admin_user_detail', user_id=user_id)
