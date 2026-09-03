from django.shortcuts import render, redirect
from django.contrib import messages


def dashboard_view(request):
   
    return render(request, 'staff/dashboard.html')

def all_users_view(request):
    # Check if user is admin
    # if not request.user.is_staff:
    #     return redirect('client_dashboard')
    
    # Get all users (you'll need a User model)
    # users = User.objects.all().order_by('-date_joined')
    
    return render(request, 'staff/admin_users.html')


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


def admin_strategies_view(request):
    # Check if user is admin
    # if not request.user.is_staff:
    #     return redirect('client_dashboard')
    
    # Get all strategies
    # strategies = Strategy.objects.all()
    
    return render(request, 'staff/admin_strategies.html')

def admin_strategy_spin_up(request, strategy_id):
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))
        reason = request.POST.get('reason', '')
        
        # Get strategy
        # strategy = get_object_or_404(Strategy, id=strategy_id)
        
        # Create price adjustment record
        # price_adjustment = PriceAdjustment.objects.create(
        #     strategy=strategy,
        #     action='spin_up',
        #     amount=amount,
        #     old_price=strategy.current_price,
        #     new_price=strategy.current_price + amount,
        #     reason=reason,
        #     admin=request.user
        # )
        
        # Update strategy price
        # strategy.current_price += amount
        # strategy.save()
        
        messages.success(request, f'Strategy price increased by ${amount}!')
    
    return redirect('staff:admin_strategies')

def admin_strategy_spin_down(request, strategy_id):
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))
        reason = request.POST.get('reason', '')
        
        # Get strategy
        # strategy = get_object_or_404(Strategy, id=strategy_id)
        
        # Create price adjustment record
        # price_adjustment = PriceAdjustment.objects.create(
        #     strategy=strategy,
        #     action='spin_down',
        #     amount=amount,
        #     old_price=strategy.current_price,
        #     new_price=strategy.current_price - amount,
        #     reason=reason,
        #     admin=request.user
        # )
        
        # Update strategy price
        # strategy.current_price -= amount
        # strategy.save()
        
        messages.warning(request, f'Strategy price decreased by ${amount}!')
    
    return redirect('staff:admin_strategies')

def admin_strategy_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        invested_coin = request.POST.get('invested_coin')
        initial_price = float(request.POST.get('initial_price'))
        risk_level = request.POST.get('risk_level')
        description = request.POST.get('description')
        min_investment = float(request.POST.get('min_investment', 100))
        management_fee = float(request.POST.get('management_fee', 1.5))
        
        # Create strategy
        # strategy = Strategy.objects.create(
        #     name=name,
        #     invested_coin=invested_coin,
        #     current_price=initial_price,
        #     risk_level=risk_level,
        #     description=description,
        #     min_investment=min_investment,
        #     management_fee=management_fee,
        #     is_active=True
        # )
        
        messages.success(request, f'Strategy "{name}" created successfully!')
    
    return redirect('staff:admin_strategies')


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


def admin_user_details(request, user_id):
    # user = get_object_or_404(User, id=user_id)
    # strategies = UserStrategy.objects.filter(user=user)
    # transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:10]
    
    return render(request, 'staff/admin_user_details.html', {'user_id': user_id})

def admin_user_edit(request, user_id):
    # user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Update user information
        # user.first_name = request.POST.get('first_name')
        # user.last_name = request.POST.get('last_name')
        # user.email = request.POST.get('email')
        # etc...
        # user.save()
        
        messages.success(request, 'User updated successfully!')
        return redirect('staff:admin_user_details', user_id=user_id)
    
    return render(request, 'staff/admin_user_edit.html', {'user_id': user_id})

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

def admin_user_update(request, user_id):
    if request.method == 'POST':
        # Handle user update
        messages.success(request, 'User updated successfully!')
        return redirect('admin_user_details', user_id=user_id)
    
    return redirect('staff:admin_users')