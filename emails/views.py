from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from .email_utils import get_base_context
from account.models import User


@staff_member_required
def email_preview(request, template_name):
    """Preview any email template in the browser"""
    # Use first user for preview, or create a dummy context
    user = User.objects.first()
    
    if not user:
        # Create dummy user context
        class DummyUser:
            first_name = "John"
            last_name = "Doe"
            email = "john.doe@example.com"
            username = "johndoe"
            balance = 12500.00
        
        user = DummyUser()
    
    context = get_base_context(user)
    
    # Add template-specific context
    if template_name == 'welcome.html' or template_name == 'verify_email.html':
        context['verify_url'] = 'http://localhost:8000/user/verify-email/abc123/'
    elif template_name == 'password_reset.html':
        context['reset_url'] = 'http://localhost:8000/user/reset-password/abc123/'
    elif template_name == 'kyc_rejected.html':
        context['rejection_reason'] = 'The document image you provided was blurry and the name on the document did not match your registered account name.'
        context['kyc_url'] = 'http://localhost:8000/user/kyc/'
    elif template_name == 'deposit_approved.html':
        class DummyDeposit:
            id = 1234
            amount = 5000.00
            def get_payment_method_display(self):
                return 'Bitcoin (BTC)'
            processed_at = None
        context['deposit'] = DummyDeposit()
    elif template_name == 'deposit_rejected.html':
        class DummyDeposit:
            id = 1234
            amount = 5000.00
            def get_payment_method_display(self):
                return 'Bitcoin (BTC)'
            rejection_reason = 'The transaction reference you provided could not be verified on the blockchain.'
        context['deposit'] = DummyDeposit()
        context['deposit_url'] = 'http://localhost:8000/user/deposit/'
    elif template_name == 'withdrawal_approved.html':
        class DummyWithdrawal:
            id = 5678
            amount = 3000.00
            network_fee = 5.00
            amount_after_fee = 2995.00
            def get_payment_method_display(self):
                return 'Bitcoin (BTC)'
            destination_address = 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh'
            transaction_hash = '0x7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t'
        context['withdrawal'] = DummyWithdrawal()
    elif template_name == 'withdrawal_rejected.html':
        class DummyWithdrawal:
            id = 5678
            amount = 3000.00
            def get_payment_method_display(self):
                return 'Bitcoin (BTC)'
            rejection_reason = 'The destination wallet address you provided appears to be invalid.'
        context['withdrawal'] = DummyWithdrawal()
        context['withdraw_url'] = 'http://localhost:8000/user/withdraw/'
    
    html_content = render_to_string(f'emails/{template_name}', context)
    return HttpResponse(html_content)


@staff_member_required
def email_preview_index(request):
    """Index page listing all email templates"""
    templates = [
        ('welcome.html', '🎉 Welcome Email'),
        ('verify_email.html', '📧 Email Verification'),
        ('password_reset.html', '🔐 Password Reset'),
        ('kyc_approved.html', '✅ KYC Approved'),
        ('kyc_rejected.html', '⚠️ KYC Rejected'),
        ('deposit_approved.html', '💰 Deposit Approved'),
        ('deposit_rejected.html', '❌ Deposit Rejected'),
        ('withdrawal_approved.html', '💸 Withdrawal Approved'),
        ('withdrawal_rejected.html', '❌ Withdrawal Rejected'),
    ]
    
    return render(request, 'emails/preview_index.html', {'templates': templates})