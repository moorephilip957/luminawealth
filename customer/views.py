from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from staff.decorators import client_login_required


login_required
@client_login_required
def dashboard_view(request):
    return render(request, 'customer/dashboard.html')

login_required
@client_login_required
def portfolio_view(request):
    return render(request, 'customer/portfolio.html')

login_required
@client_login_required
def strategies_view(request):
    return render(request, 'customer/strategies.html')

login_required
@client_login_required
def strategy_details(request):
    return render(request, 'customer/strategy_details.html')

login_required
@client_login_required
def deposit_view(request):
    return render(request, 'customer/deposit_request.html')

login_required
@client_login_required
def deposit_submit(request):
    if request.method == 'POST':
        # Get form data
        amount = request.POST.get('amount')
        method = request.POST.get('method')
        currency = request.POST.get('currency', 'USD')
        notes = request.POST.get('notes', '')
        
        # Here you would save to database
        # deposit_request = DepositRequest.objects.create(
        #     user=request.user,
        #     amount=amount,
        #     method=method,
        #     currency=currency,
        #     notes=notes,
        #     status='pending'
        # )
        
        # For now, just render success page with the data
        method_display = {
            'crypto_btc': 'Bitcoin (BTC)',
            'crypto_eth': 'Ethereum (ETH)',
            'crypto_usdt': 'USDT (TRC20)',
            'bank_wire': 'Bank Wire Transfer',
            'bank_sepa': 'Bank Transfer (SEPA)',
            'card': 'Credit/Debit Card',
            'other': 'Other'
        }
        
        context = {
            'amount': f"{float(amount):,.2f}",
            'method': method_display.get(method, method)
        }
        
        return render(request, 'customer/deposit_success.html', context)
    
    return redirect('customer:deposit')

login_required
@client_login_required
def withdraw_view(request):
    return render(request, 'customer/withdraw.html')

login_required
@client_login_required
def withdraw_submit(request):
    if request.method == 'POST':
        # Get form data
        amount = request.POST.get('amount')
        method = request.POST.get('method')
        notes = request.POST.get('notes', '')
        
        # Get destination details based on method
        if method.startswith('crypto_'):
            destination = request.POST.get('wallet_address', '')
        else:
            account_name = request.POST.get('account_name', '')
            account_number = request.POST.get('account_number', '')
            destination = f"{account_name} - {account_number}"
        
        # Here you would save to database
        # withdrawal_request = WithdrawalRequest.objects.create(
        #     user=request.user,
        #     amount=amount,
        #     method=method,
        #     destination=destination,
        #     notes=notes,
        #     status='pending'
        # )
        
        # For now, just render success page with the data
        method_display = {
            'crypto_btc': 'Bitcoin (BTC)',
            'crypto_eth': 'Ethereum (ETH)',
            'crypto_usdt': 'USDT (TRC20)',
            'bank_wire': 'Bank Wire Transfer',
            'bank_sepa': 'Bank Transfer (SEPA)'
        }
        
        context = {
            'amount': f"{float(amount):,.2f}",
            'method': method_display.get(method, method)
        }
        
        return render(request, 'customer/withdraw_success.html', context)
    
    return redirect('customer:withdraw')

login_required
@client_login_required
def profile_view(request):
    return render(request, 'customer/profile.html')

login_required
@client_login_required
def profile_settings(request):
    return render(request, 'customer/profile_settings.html')

login_required
@client_login_required
def profile_settings_update(request):
    if request.method == 'POST':
        # Handle personal info update
        # first_name = request.POST.get('first_name')
        # last_name = request.POST.get('last_name')
        # email = request.POST.get('email')
        # phone = request.POST.get('phone')
        # timezone = request.POST.get('timezone')
        
        # Update user profile in database
        # request.user.first_name = first_name
        # request.user.last_name = last_name
        # request.user.email = email
        # request.user.profile.phone = phone
        # request.user.profile.timezone = timezone
        # request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
    
    return redirect('customer:profile_settings')

login_required
@client_login_required
def profile_password_update(request):
    if request.method == 'POST':
        # Handle password change
        # current_password = request.POST.get('current_password')
        # new_password = request.POST.get('new_password')
        # confirm_password = request.POST.get('confirm_password')
        
        # Verify current password and update to new password
        # if request.user.check_password(current_password):
        #     if new_password == confirm_password:
        #         request.user.set_password(new_password)
        #         request.user.save()
        #         messages.success(request, 'Password updated successfully!')
        #     else:
        #         messages.error(request, 'New passwords do not match.')
        # else:
        #     messages.error(request, 'Current password is incorrect.')
        
        messages.success(request, 'Password updated successfully!')
    
    return redirect('customer:profile_settings')

login_required
@client_login_required
def profile_notifications_update(request):
    if request.method == 'POST':
        # Handle notification preferences
        # email_deposits = request.POST.get('email_deposits') == 'on'
        # email_withdrawals = request.POST.get('email_withdrawals') == 'on'
        # etc...
        
        # Update notification settings in database
        
        messages.success(request, 'Notification settings updated!')
    
    return redirect('customer:profile_settings')

login_required
@client_login_required
def kyc_view(request):
    return render(request, 'customer/kyc.html')

login_required
@client_login_required
def kyc_address_submit(request):
    if request.method == 'POST':
        # Handle address document upload
        # doc_type = request.POST.get('address_doc_type')
        # document = request.FILES.get('address_document')
        
        # Save to database
        # kyc_doc = KYCDocument.objects.create(
        #     user=request.user,
        #     doc_type='address_proof',
        #     sub_type=doc_type,
        #     file=document,
        #     status='pending_review'
        # )
        
        messages.success(request, 'Address proof submitted successfully!')
    
    return redirect('customer:kyc')

login_required
@client_login_required
def notifications_view(request):
    return render(request, 'customer/notifications.html')

login_required
@client_login_required
def transaction_history(request):
    return render(request, 'customer/transaction_history.html')

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
