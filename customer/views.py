from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from staff.decorators import client_login_required
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from datetime import timedelta
import re
from django.contrib.auth import update_session_auth_hash


from coin.models import Strategy, StrategyInvestor, SpinRecord
from transaction.models import Transaction, DepositRequest, WithdrawalRequest
from account.decorators import kyc_required
from account.models import TrustedDevice
from account.models import User
from kyc.models import KYCSubmission


@login_required
@client_login_required
def dashboard_view(request):
    user = request.user
    
    # 1. Get Active Investments
    active_investments = StrategyInvestor.objects.filter(
        user=user, 
        status='active'
    ).select_related('strategy').order_by('-current_value')
    
    total_invested = active_investments.aggregate(total=Sum('invested_amount'))['total'] or 0
    total_current_value = active_investments.aggregate(total=Sum('current_value'))['total'] or 0
    total_profit = total_current_value - total_invested
    
    # Calculate profit percentage safely
    profit_percent = (total_profit / total_invested * 100) if total_invested > 0 else 0
    
    # 2. Balance Info
    available_balance = user.balance
    total_portfolio_value = available_balance + total_current_value
    
    # 3. Recent Transactions (Last 5)
    recent_transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:5]
    
    # 4. Asset Allocation Data for Chart
    allocation_data = []
    colors = ['#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ef4444']
    
    # Add top 4 active strategies
    for i, inv in enumerate(active_investments[:4]):
        allocation_data.append({
            'label': inv.strategy.name,
            'value': float(inv.current_value),
            'color': colors[i % len(colors)]
        })
    
    # Always add available cash to the chart if > 0
    if available_balance > 0:
        allocation_data.append({
            'label': 'Available Cash',
            'value': float(available_balance),
            'color': '#6b7280'
        })
    
    # Fallback if user has absolutely nothing
    if not allocation_data:
        allocation_data.append({'label': 'No Data', 'value': 0, 'color': '#6b7280'})
    
    context = {
        'total_portfolio_value': total_portfolio_value,
        'total_profit': total_profit,
        'profit_percent': profit_percent,
        'available_balance': available_balance,
        'active_investments': active_investments,
        'recent_transactions': recent_transactions,
        'allocation_data': allocation_data,
    }
    
    return render(request, 'customer/dashboard.html', context)

login_required
@client_login_required
def portfolio_view(request):
    user = request.user
    
    # Get all user investments (active and paused)
    investments = StrategyInvestor.objects.filter(
        user=user
    ).select_related('strategy').order_by('-current_value')
    
    # Calculate portfolio metrics
    total_invested = investments.aggregate(total=Sum('invested_amount'))['total'] or 0
    total_current_value = investments.aggregate(total=Sum('current_value'))['total'] or 0
    total_profit = total_current_value - total_invested
    profit_percent = (total_profit / total_invested * 100) if total_invested > 0 else 0
    
    available_cash = user.balance
    total_portfolio_value = available_cash + total_current_value
    
    # Prepare allocation data for the doughnut chart
    allocation_data = []
    colors = ['#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ef4444']
    
    # Add top 5 investments
    for i, inv in enumerate(investments[:5]):
        allocation_data.append({
            'label': inv.strategy.name,
            'value': float(inv.current_value),
            'color': colors[i % len(colors)]
        })
        
    # Always add available cash to the chart if > 0
    if available_cash > 0:
        allocation_data.append({
            'label': 'Available Cash',
            'value': float(available_cash),
            'color': '#6b7280'
        })
        
    # Fallback if user has absolutely nothing
    if not allocation_data:
        allocation_data.append({'label': 'No Data', 'value': 0, 'color': '#6b7280'})

    context = {
        'total_portfolio_value': total_portfolio_value,
        'total_invested': total_invested,
        'total_profit': total_profit,
        'profit_percent': profit_percent,
        'available_cash': available_cash,
        'investments': investments,
        'allocation_data': allocation_data,
    }
    
    return render(request, 'customer/portfolio.html', context)

@login_required
@client_login_required
def strategies_view(request):
    # Fetch only active and public strategies
    strategies = Strategy.objects.filter(status='active', is_public=True)
    
    # 1. Filtering by risk level
    risk_filter = request.GET.get('risk', 'all')
    if risk_filter != 'all':
        strategies = strategies.filter(risk_level=risk_filter)
        
    # 2. Sorting
    sort_by = request.GET.get('sort', 'popular')
    if sort_by == 'roi':
        strategies = strategies.order_by('-ai_accuracy')
    elif sort_by == 'popular':
        strategies = strategies.order_by('-total_investors')
    elif sort_by == 'minimum':
        strategies = strategies.order_by('min_investment')
    else:
        strategies = strategies.order_by('-created_at')  # Default fallback
        
    context = {
        'strategies': strategies,
        'risk_filter': risk_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'customer/strategies.html', context)

@login_required
@client_login_required
def strategy_detail_view(request, strategy_id):
    strategy = get_object_or_404(Strategy, id=strategy_id, is_public=True)
    
    # 1. Check if user has ANY investment record for this strategy (active OR liquidated)
    user_investment = StrategyInvestor.objects.filter(
        user=request.user,
        strategy=strategy
    ).first()
    
    # --- Chart Data Preparation (Last 30 Days) ---
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    spin_records = SpinRecord.objects.filter(
        strategy=strategy,
        created_at__gte=thirty_days_ago
    ).order_by('created_at')
    
    chart_labels = [spin.created_at.strftime('%b %d') for spin in spin_records]
    chart_data = [float(spin.new_price) for spin in spin_records]
    
    if not chart_data:
        chart_labels = ['Inception', 'Current']
        chart_data = [float(strategy.initial_price), float(strategy.current_price)]
        
    # --- Calculate Metrics ---
    all_time_roi = ((strategy.current_price - strategy.initial_price) / strategy.initial_price * 100) if strategy.initial_price > 0 else 0
    
    old_spin = SpinRecord.objects.filter(strategy=strategy, created_at__lte=thirty_days_ago).order_by('-created_at').first()
    roi_30d = ((strategy.current_price - old_spin.new_price) / old_spin.new_price * 100) if (old_spin and old_spin.new_price > 0) else all_time_roi

    # ==========================================
    # HANDLE "START INVESTING" FORM SUBMISSION
    # ==========================================
    if request.method == 'POST' and 'invest_amount' in request.POST:
        amount_str = request.POST.get('invest_amount')
        try:
            amount = Decimal(amount_str)
            
            # Validations
            if amount < strategy.min_investment:
                messages.error(request, f"Minimum investment for this strategy is ${strategy.min_investment:.2f}.")
            elif amount > request.user.balance:
                messages.error(request, f"Insufficient balance. You have ${request.user.balance:.2f} available.")
            else:
                # 1. Deduct balance and update total invested
                request.user.balance -= amount
                request.user.total_invested += amount
                request.user.save(update_fields=['balance', 'total_invested', 'updated_at'])
                
                # 2. Calculate new shares to add
                new_shares = amount / strategy.current_price if strategy.current_price > 0 else Decimal('0')
                
                if user_investment:
                    if user_investment.status == 'liquidated':
                        # REACTIVATE: Treat as a fresh investment for tracking purposes, 
                        # but keep the same database record for audit continuity.
                        user_investment.status = 'active'
                        user_investment.liquidated_at = None
                        user_investment.invested_amount = amount       # Reset to new amount
                        user_investment.shares = new_shares            # Reset to new shares
                        user_investment.current_value = amount         # Starts at break-even
                        user_investment.total_profit = Decimal('0')    # Reset profit tracking
                        user_investment.invested_at = timezone.now()   # Reset start date to now
                    else:
                        # ALREADY ACTIVE: Just add to the existing position
                        user_investment.invested_amount += amount
                        user_investment.shares += new_shares
                        
                    # Recalculate current value and profit based on total shares and current price
                    user_investment.current_value = user_investment.shares * strategy.current_price
                    user_investment.total_profit = user_investment.current_value - user_investment.invested_amount
                    
                    user_investment.save(update_fields=[
                        'status', 'liquidated_at', 'invested_amount', 'shares', 
                        'current_value', 'total_profit', 'invested_at', 'updated_at'
                    ])
                else:
                    # 3. Create NEW StrategyInvestor record (first time investing)
                    StrategyInvestor.objects.create(
                        user=request.user,
                        strategy=strategy,
                        invested_amount=amount,
                        shares=new_shares,
                        current_value=amount,
                        total_profit=Decimal('0'),
                        status='active',
                        invested_at=timezone.now()
                    )
                
                # 4. Create Transaction record
                Transaction.create_transaction(
                    user=request.user,
                    transaction_type=Transaction.TYPE_INVESTMENT,
                    amount=amount,
                    description=f"Investment in {strategy.name}",
                    status=Transaction.STATUS_COMPLETED
                )
                
                messages.success(request, f"✅ Successfully invested ${amount:.2f} in {strategy.name}!")
                return redirect('customer:strategy_detail', strategy_id=strategy.id)
                
        except (InvalidOperation, ValueError, TypeError):
            messages.error(request, "Please enter a valid investment amount.")
        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
            print(f"Investment error: {e}")

    context = {
        'strategy': strategy,
        'user_investment': user_investment,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'all_time_roi': all_time_roi,
        'roi_30d': roi_30d,
    }
    
    return render(request, 'customer/strategy_details.html', context)


@login_required
@client_login_required
def add_funds_to_strategy(request, strategy_id):
    """
    Handle adding funds to an EXISTING ACTIVE strategy investment.
    """
    strategy = get_object_or_404(Strategy, id=strategy_id, is_public=True)
    
    # Ensure the user has an ACTIVE investment in this specific strategy
    investment = get_object_or_404(
        StrategyInvestor, 
        user=request.user, 
        strategy=strategy, 
        status='active'
    )
    
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        try:
            amount = Decimal(amount_str)
            
            # Validations
            if amount <= 0:
                messages.error(request, "Amount must be greater than 0.")
            elif amount < strategy.min_investment:
                messages.error(request, f"Minimum additional investment is ${strategy.min_investment:.2f}.")
            elif amount > request.user.balance:
                messages.error(request, f"Insufficient balance. You have ${request.user.balance:.2f} available.")
            else:
                # 1. Deduct balance and update total invested
                request.user.balance -= amount
                request.user.total_invested += amount
                request.user.save(update_fields=['balance', 'total_invested', 'updated_at'])
                
                # 2. Calculate new shares to add at the CURRENT price
                new_shares = amount / strategy.current_price if strategy.current_price > 0 else Decimal('0')
                
                # 3. Update the existing investment record
                investment.invested_amount += amount
                investment.shares += new_shares
                investment.current_value = investment.shares * strategy.current_price
                investment.total_profit = investment.current_value - investment.invested_amount
                investment.save(update_fields=[
                    'invested_amount', 'shares', 'current_value', 'total_profit', 'updated_at'
                ])
                
                # 4. Create Transaction record
                Transaction.create_transaction(
                    user=request.user,
                    transaction_type=Transaction.TYPE_INVESTMENT,
                    amount=amount,
                    description=f"Added funds to {strategy.name}",
                    status=Transaction.STATUS_COMPLETED
                )
                
                messages.success(request, f"✅ Successfully added ${amount:.2f} to {strategy.name}!")
                return redirect('customer:portfolio')
                
        except (InvalidOperation, ValueError, TypeError):
            messages.error(request, "Please enter a valid investment amount.")
        except Exception as e:
            messages.error(request, "An unexpected error occurred. Please try again.")
            print(f"Add funds error: {e}")
            
    context = {
        'strategy': strategy,
        'investment': investment,
    }
    
    return render(request, 'customer/add_funds.html', context)

@login_required
@client_login_required
def strategy_liquidate_view(request, strategy_id):
    """
    Handle the liquidation of an active strategy investment.
    """
    strategy = get_object_or_404(Strategy, id=strategy_id, is_public=True)
    investment = get_object_or_404(
        StrategyInvestor, 
        user=request.user, 
        strategy=strategy, 
        status='active'
    )
    
    if request.method == 'POST':
        try:
            # 1. Recalculate current value based on latest strategy price
            current_value = investment.shares * strategy.current_price
            profit_loss = current_value - investment.invested_amount
            
            # 2. Update investment record
            investment.status = 'liquidated'
            investment.liquidated_at = timezone.now()
            investment.current_value = current_value
            investment.total_profit = profit_loss
            investment.save(update_fields=['status', 'liquidated_at', 'current_value', 'total_profit', 'updated_at'])
            
            # 3. Return funds to user balance
            request.user.balance += current_value
            request.user.total_invested -= investment.invested_amount
            request.user.save(update_fields=['balance', 'total_invested', 'updated_at'])
            
            # 4. Create Transaction record
            Transaction.create_transaction(
                user=request.user,
                transaction_type=Transaction.TYPE_LIQUIDATION,
                amount=current_value,
                description=f"Liquidation of {strategy.name}",
                status=Transaction.STATUS_COMPLETED
            )
            
            messages.success(
                request, 
                f"✅ Position liquidated successfully! ${current_value:.2f} has been returned to your available balance."
            )
            return redirect('customer:portfolio')
            
        except Exception as e:
            messages.error(request, "An error occurred during liquidation. Please try again.")
            print(f"Liquidation error: {e}")
            
    return redirect('customer:strategy_detail', strategy_id=strategy.id)

# Map template method values to model choices (card removed)
METHOD_MAPPING = {
    'crypto_btc': 'btc',
    'crypto_eth': 'eth',
    'crypto_usdt': 'usdt',
    'bank_wire': 'bank_wire',
    'bank_sepa': 'sepa',
    'other': 'bank_wire',  # Default fallback for "Other"
}

@login_required
@client_login_required
def deposit_view(request):
    """
    Handle client deposit requests.
    Creates a pending DepositRequest, which automatically creates a pending Transaction.
    """
    if request.method == 'POST':
        amount = request.POST.get('amount')
        method = request.POST.get('method')
        currency = request.POST.get('currency', 'USD')
        notes = request.POST.get('notes', '').strip()

        # 1. Validate Amount
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0")
            if amount < 50:
                raise ValueError("Minimum deposit amount is $50.00")
        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid deposit amount (Minimum $50.00).")
            return redirect('customer:deposit')

        # 2. Validate and Map Payment Method
        payment_method = METHOD_MAPPING.get(method)
        if not payment_method:
            messages.error(request, "Please select a valid payment method.")
            return redirect('customer:deposit')

        # 3. Create Deposit Request
        try:
            deposit = DepositRequest.objects.create(
                user=request.user,
                amount=amount,
                payment_method=payment_method,
                transaction_reference=notes[:200] if notes else '',
                # sender_details=f"Currency: {currency}",
                # ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # The DepositRequest.save() method automatically creates the pending Transaction!
            
            messages.success(
                request, 
                f"✅ Deposit request of ${amount:.2f} submitted successfully! "
                f"Our team will review it shortly."
            )
            return redirect('customer:dashboard')
            
        except Exception as e:
            messages.error(request, f"An error occurred while submitting your deposit. Please try again.")
            print(f"Deposit error: {e}")
            return redirect('customer:deposit')

    # GET request: fetch recent deposits for the sidebar
    recent_deposits = DepositRequest.objects.filter(user=request.user).order_by('-created_at')[:3]
    
    context = {
        'recent_deposits': recent_deposits,
    }
    
    return render(request, 'customer/deposit_request.html', context)


# Map template method values to model choices
WITHDRAWAL_METHOD_MAPPING = {
    'crypto_btc': 'btc',
    'crypto_eth': 'eth',
    'crypto_usdt': 'usdt',
    'bank_wire': 'bank_wire',
    'bank_sepa': 'sepa',
}

# Network fees for crypto withdrawals (demo purposes)
NETWORK_FEES = {
    'btc': Decimal('5.00'),
    'eth': Decimal('3.00'),
    'usdt': Decimal('1.00'),
    'bank_wire': Decimal('15.00'),
    'sepa': Decimal('5.00'),
}

login_required
@client_login_required
@kyc_required
def withdraw_view(request):
    """
    Handle client withdrawal requests.
    Requires KYC approval. Creates a pending WithdrawalRequest,
    which automatically creates a pending Transaction.
    """
    user = request.user
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        method = request.POST.get('method')
        notes = request.POST.get('notes', '').strip()
        
        # 1. Validate Amount
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise InvalidOperation("Amount must be greater than 0")
            if amount < 50:
                raise InvalidOperation("Minimum withdrawal amount is $50.00")
            if amount > user.balance:
                messages.error(
                    request,
                    f"Insufficient balance. You have ${user.balance:.2f} available."
                )
                return redirect('customer:withdraw')
        except (InvalidOperation, ValueError, TypeError):
            messages.error(request, "Please enter a valid withdrawal amount.")
            return redirect('customer:withdraw')

        # 2. Validate and Map Payment Method
        payment_method = WITHDRAWAL_METHOD_MAPPING.get(method)
        if not payment_method:
            messages.error(request, "Please select a valid withdrawal method.")
            return redirect('customer:withdraw')

        # 3. Get Destination Details (crypto vs bank)
        destination_address = ''
        destination_name = ''
        network = ''
        
        if payment_method in ['btc', 'eth', 'usdt']:
            # Crypto withdrawal - need wallet address
            wallet_address = request.POST.get('wallet_address', '').strip()
            if not wallet_address:
                messages.error(request, "Please enter your wallet address.")
                return redirect('customer:withdraw')
            destination_address = wallet_address
            
            # Set network based on coin
            if payment_method == 'btc':
                network = 'Bitcoin Mainnet'
            elif payment_method == 'eth':
                network = 'Ethereum (ERC20)'
            elif payment_method == 'usdt':
                network = 'TRON (TRC20)'
                
        elif payment_method in ['bank_wire', 'sepa']:
            # Bank withdrawal - need account details
            account_name = request.POST.get('account_name', '').strip()
            account_number = request.POST.get('account_number', '').strip()
            bank_name = request.POST.get('bank_name', '').strip()
            routing_number = request.POST.get('routing_number', '').strip()
            
            if not all([account_name, account_number, bank_name, routing_number]):
                messages.error(request, "Please fill in all bank account details.")
                return redirect('customer:withdraw')
            
            # Combine bank details into destination_address field
            destination_address = (
                f"Bank: {bank_name} | "
                f"Account: {account_number} | "
                f"Routing: {routing_number}"
            )
            destination_name = account_name

        # 4. Calculate network fee
        network_fee = NETWORK_FEES.get(payment_method, Decimal('0.00'))
        
        # 5. Create Withdrawal Request
        try:
            withdrawal = WithdrawalRequest.objects.create(
                user=user,
                amount=amount,
                payment_method=payment_method,
                destination_address=destination_address,
                destination_name=destination_name,
                network=network,
                network_fee=network_fee,
                # sender_details=notes if notes else '',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            
            # The WithdrawalRequest.save() method automatically creates the pending Transaction!
            
            amount_after_fee = amount - network_fee
            messages.success(
                request,
                f"✅ Withdrawal request of ${amount:.2f} submitted successfully! "
                f"After network fee (${network_fee:.2f}), you'll receive ${amount_after_fee:.2f}. "
                f"Our team will process it shortly."
            )
            return redirect('customer:dashboard')
            
        except Exception as e:
            messages.error(request, f"An error occurred while submitting your withdrawal. Please try again.")
            print(f"Withdrawal error: {e}")
            return redirect('customer:withdraw')

    # GET request: fetch recent withdrawals for the sidebar
    recent_withdrawals = WithdrawalRequest.objects.filter(user=user).order_by('-created_at')[:3]
    
    context = {
        'recent_withdrawals': recent_withdrawals,
    }
    
    return render(request, 'customer/withdraw.html', context)

@login_required
@client_login_required
def profile_view(request):
    user = request.user
    
    # Get recent trusted devices (login activity)
    recent_devices = TrustedDevice.objects.filter(
        user=user, 
        is_active=True
    ).select_related('user').order_by('-last_used_at')[:5]
    
    context = {
        'recent_devices': recent_devices,
    }
    
    return render(request, 'customer/profile.html', context)

@login_required
@client_login_required
def profile_settings_view(request):
    """
    Handle profile settings: personal info, password, and notifications.
    """
    user = request.user
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'personal_info':
            return handle_personal_info_update(request, user)
        elif form_type == 'password_change':
            return handle_password_change(request, user)
        elif form_type == 'notifications':
            return handle_notification_update(request, user)
        elif form_type == 'delete_account':
            return handle_account_deletion(request, user)
    
    context = {
        'user': user,
    }
    
    return render(request, 'customer/profile_settings.html', context)


def handle_personal_info_update(request, user):
    """Update personal information including profile picture"""
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    email = request.POST.get('email', '').strip().lower()
    phone = request.POST.get('phone', '').strip()
    timezone = request.POST.get('timezone', 'UTC')
    
    # Validate required fields
    if not first_name or not last_name or not email:
        messages.error(request, 'First name, last name, and email are required.')
        return redirect('customer:profile_settings')
    
    # Handle profile picture upload
    if 'profile_picture' in request.FILES:
        picture = request.FILES['profile_picture']
        
        # Validate file size (max 2MB)
        if picture.size > 2 * 1024 * 1024:
            messages.error(request, 'Profile picture must be less than 2MB.')
            return redirect('customer:profile_settings')
        
        # Validate file type
        if not picture.content_type in ['image/jpeg', 'image/jpg', 'image/png']:
            messages.error(request, 'Profile picture must be a JPG or PNG image.')
            return redirect('customer:profile_settings')
        
        # Delete old picture if exists
        if user.profile_picture:
            try:
                user.profile_picture.delete(save=False)
            except Exception as e:
                print(f"Error deleting old profile picture: {e}")
        
        user.profile_picture = picture
    
    # Handle picture removal
    if request.POST.get('remove_picture') == '1':
        if user.profile_picture:
            try:
                user.profile_picture.delete(save=False)
            except Exception as e:
                print(f"Error deleting profile picture: {e}")
        user.profile_picture = None
    
    # Check if email is being changed
    email_changed = email != user.email
    
    if email_changed:
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, 'This email address is already in use.')
            return redirect('customer:profile_settings')
        
        user.username = email
        user.email = email
        user.email_verified = False
        messages.warning(request, 'Email updated. Please check your inbox to verify your new email address.')
    
    # Update user fields
    user.first_name = first_name
    user.last_name = last_name
    user.phone = phone
    user.timezone = timezone
    user.save()
    
    messages.success(request, '✅ Personal information updated successfully!')
    return redirect('customer:profile_settings')


def handle_password_change(request, user):
    """Change user password"""
    current_password = request.POST.get('current_password', '')
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')
    
    # Verify current password
    if not user.check_password(current_password):
        messages.error(request, 'Current password is incorrect.')
        return redirect('customer:profile_settings')
    
    # Validate new password
    if len(new_password) < 8:
        messages.error(request, 'Password must be at least 8 characters long.')
        return redirect('customer:profile_settings')
    
    if not re.search(r'[A-Z]', new_password):
        messages.error(request, 'Password must contain at least one uppercase letter.')
        return redirect('customer:profile_settings')
    
    if not re.search(r'[a-z]', new_password):
        messages.error(request, 'Password must contain at least one lowercase letter.')
        return redirect('customer:profile_settings')
    
    if not re.search(r'\d', new_password):
        messages.error(request, 'Password must contain at least one number.')
        return redirect('customer:profile_settings')
    
    # Check passwords match
    if new_password != confirm_password:
        messages.error(request, 'New passwords do not match.')
        return redirect('customer:profile_settings')
    
    # Update password
    user.set_password(new_password)
    user.save()
    
    # Keep user logged in after password change
    update_session_auth_hash(request, user)
    
    messages.success(request, '✅ Password updated successfully!')
    return redirect('customer:profile_settings')


def handle_notification_update(request, user):
    """Update notification preferences"""
    # For now, just show success message
    # In production, you'd save these to a UserPreferences model
    messages.success(request, '✅ Notification preferences updated successfully!')
    return redirect('customer:profile_settings')


def handle_account_deletion(request, user):
    """Delete user account after confirmation"""
    confirmation = request.POST.get('delete_confirm', '')
    
    if confirmation != 'DELETE':
        messages.error(request, 'Please type DELETE to confirm account deletion.')
        return redirect('customer:profile_settings')
    
    # In production, you'd want to:
    # 1. Liquidate all active investments
    # 2. Return funds to user
    # 3. Process pending withdrawals
    # 4. Anonymize or delete user data based on legal requirements
    
    # For now, just deactivate the account
    user.is_active = False
    user.save()
    
    # Log out the user
    from django.contrib.auth import logout
    logout(request)
    
    messages.success(request, 'Your account has been successfully deleted. Thank you for using LuminaWealthAI.')
    return redirect('home')


@login_required
@client_login_required
def kyc_view(request):
    user = request.user
    kyc_submission = KYCSubmission.objects.filter(user=user).order_by('-submitted_at').first()
    
    if request.method == 'POST':
        if not kyc_submission:
            kyc_submission = KYCSubmission(user=user)
        
        # ============================================
        # STEP 2: ID Document Submission
        # ============================================
        if 'document_type' in request.POST:
            kyc_submission.document_type = request.POST.get('document_type')
            kyc_submission.document_number = request.POST.get('document_number', '')
            
            if 'document_front' in request.FILES:
                kyc_submission.document_front = request.FILES.get('document_front')
            if 'document_back' in request.FILES:
                kyc_submission.document_back = request.FILES.get('document_back')
            
            # Safe fallbacks for required fields to prevent NOT NULL errors
            if not kyc_submission.full_name:
                kyc_submission.full_name = user.get_full_name() or user.username
            if not kyc_submission.date_of_birth:
                from datetime import date
                kyc_submission.date_of_birth = date(1990, 1, 1) 
            if not kyc_submission.nationality:
                kyc_submission.nationality = request.POST.get('nationality', 'Not Specified')
            if not kyc_submission.residential_address:
                kyc_submission.residential_address = request.POST.get('residential_address', 'Not Specified')
            
            kyc_submission.id_needs_resubmit = False
            kyc_submission.save()
            messages.success(request, "✅ ID document submitted successfully!")
            return redirect('customer:kyc')
        
        # ============================================
        # STEP 3: Address Proof Submission
        # ============================================
        if 'address_doc_type' in request.POST:
            kyc_submission.address_doc_type = request.POST.get('address_doc_type')
            if 'address_document' in request.FILES:
                kyc_submission.proof_of_address = request.FILES.get('address_document')
            
            kyc_submission.address_needs_resubmit = False
            kyc_submission.save()
            messages.success(request, "✅ Address proof submitted successfully!")
            return redirect('customer:kyc')
        
        # ============================================
        # STEP 4: Selfie Submission
        # ============================================
        if 'selfie_document' in request.FILES:
            kyc_submission.selfie = request.FILES.get('selfie_document')
            kyc_submission.selfie_needs_resubmit = False
            kyc_submission.save()
            messages.success(request, "✅ Selfie submitted successfully!")
            return redirect('customer:kyc')

    # ============================================
    # CHECK IF ALL STEPS ARE FRESHLY SUBMITTED
    # ============================================
    if kyc_submission:
        all_docs_exist = (kyc_submission.document_front and kyc_submission.proof_of_address and kyc_submission.selfie)
        all_steps_fresh = (not kyc_submission.id_needs_resubmit and not kyc_submission.address_needs_resubmit and not kyc_submission.selfie_needs_resubmit)
        
        if all_docs_exist and all_steps_fresh:
            if kyc_submission.status in [KYCSubmission.STATUS_REJECTED, KYCSubmission.STATUS_RESUBMISSION, KYCSubmission.STATUS_PENDING]:
                if kyc_submission.status in [KYCSubmission.STATUS_REJECTED, KYCSubmission.STATUS_RESUBMISSION]:
                    kyc_submission.resubmission_count += 1
                
                kyc_submission.status = KYCSubmission.STATUS_UNDER_REVIEW
                kyc_submission.reviewed_by = None
                kyc_submission.reviewed_at = None
                kyc_submission.rejection_reason = ''
                kyc_submission.save()
                messages.success(request, "🎉 All documents submitted! Your KYC is now under review.")
                return redirect('customer:kyc')

    # ============================================
    # DYNAMIC PROGRESS & STEP CALCULATION
    # ============================================
    if kyc_submission and kyc_submission.status in [KYCSubmission.STATUS_REJECTED, KYCSubmission.STATUS_RESUBMISSION]:
        # Rejected state: dynamically calculate progress based on which flags are cleared
        steps_completed = 1
        progress_percentage = 25
        current_step = 2 
        
        if not kyc_submission.id_needs_resubmit and kyc_submission.document_front:
            steps_completed = 2
            progress_percentage = 50
            current_step = 3  # Advance to 3!
            
        if not kyc_submission.address_needs_resubmit and kyc_submission.proof_of_address:
            steps_completed = 3
            progress_percentage = 75
            current_step = 4  # Advance to 4!
            
        if not kyc_submission.selfie_needs_resubmit and kyc_submission.selfie:
            steps_completed = 4
            progress_percentage = 100
            current_step = 5  # Advance to 5!
    else:
        # Normal progress calculation
        steps_completed = 0
        if user.first_name and user.last_name: steps_completed += 1
        if kyc_submission and kyc_submission.document_front and not kyc_submission.id_needs_resubmit: steps_completed += 1
        if kyc_submission and kyc_submission.proof_of_address and not kyc_submission.address_needs_resubmit: steps_completed += 1
        if kyc_submission and kyc_submission.selfie and not kyc_submission.selfie_needs_resubmit: steps_completed += 1
            
        progress_percentage = int((steps_completed / 4) * 100)
        
        current_step = 1
        if user.first_name and user.last_name: current_step = 2
        if kyc_submission and kyc_submission.document_front and not kyc_submission.id_needs_resubmit: current_step = 3
        if kyc_submission and kyc_submission.proof_of_address and not kyc_submission.address_needs_resubmit: current_step = 4
        if kyc_submission and kyc_submission.selfie and not kyc_submission.selfie_needs_resubmit: current_step = 5

    context = {
        'kyc_submission': kyc_submission,
        'user': user,
        'steps_completed': steps_completed,
        'progress_percentage': progress_percentage,
        'current_step': current_step,
    }
    return render(request, 'customer/kyc.html', context)


login_required
@client_login_required
def notifications_view(request):
    return render(request, 'customer/notifications.html')

@login_required
@client_login_required
def transaction_history(request):
    user = request.user
    
    # Base queryset: only this user's transactions, ordered newest first
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')
    
    # --- Server-Side Filtering ---
    type_filter = request.GET.get('type', 'all')
    status_filter = request.GET.get('status', 'all')
    date_filter = request.GET.get('date', 'all')
    search_query = request.GET.get('search', '')
    
    if type_filter != 'all':
        transactions = transactions.filter(transaction_type=type_filter)
        
    if status_filter != 'all':
        transactions = transactions.filter(status=status_filter)
        
    if date_filter == 'today':
        transactions = transactions.filter(created_at__date=timezone.now().date())
    elif date_filter == 'week':
        transactions = transactions.filter(created_at__gte=timezone.now() - timedelta(days=7))
    elif date_filter == 'month':
        transactions = transactions.filter(created_at__gte=timezone.now() - timedelta(days=30))
    elif date_filter == 'year':
        transactions = transactions.filter(created_at__gte=timezone.now() - timedelta(days=365))
        
    if search_query:
        transactions = transactions.filter(
            Q(reference__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # --- Calculate Stats (Always based on COMPLETED transactions for accuracy) ---
    completed_txns = Transaction.objects.filter(user=user, status=Transaction.STATUS_COMPLETED)
    
    total_deposits = completed_txns.filter(
        transaction_type=Transaction.TYPE_DEPOSIT
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_withdrawals = completed_txns.filter(
        transaction_type=Transaction.TYPE_WITHDRAWAL
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_invested = completed_txns.filter(
        transaction_type=Transaction.TYPE_INVESTMENT
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Total profit: Sum of all strategy returns (liquidations return principal + profit, so we just track returns for pure profit stat)
    total_profit = completed_txns.filter(
        transaction_type=Transaction.TYPE_STRATEGY_RETURN
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'transactions': transactions,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_invested': total_invested,
        'total_profit': total_profit,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search_query': search_query,
    }
    
    return render(request, 'customer/transaction_history.html', context)

login_required
@client_login_required
def email_verification_prompt_view(request):
    """
    Show a prompt page asking user to verify their email.
    """
    return render(request, 'customer/email_verification_prompt.html')

login_required
@client_login_required
def kyc_status_view(request):
    """
    Show KYC status page when KYC is pending.
    """
    return render(request, 'customer/kyc_status.html')

login_required
def account_suspended_view(request):
    """
    Display account suspended page.
    """
    # 1. If completely logged out, send to login
    if not request.user.is_authenticated:
        return redirect('account:login')
    
    # 2. If they are active, they shouldn't be here. Send to dashboard.
    if getattr(request.user, 'account_status', 'active') != 'suspended':
        return redirect('customer:dashboard') # Adjust to your dashboard namespace
    
    # 3. They are logged in AND suspended. Show the page safely.
    context = {
        'suspension_reason': getattr(request.user, 'suspension_reason', None) or 'Your account has been suspended.',
        'suspended_at': getattr(request.user, 'suspended_at', None),
        'suspended_by': getattr(request.user, 'suspended_by', None),
    }
    
    return render(request, 'customer/account_suspended.html', context)
