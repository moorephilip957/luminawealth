from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_templated_email(subject, template_name, context, recipient_list, 
                         from_email=None, fail_silently=False):
    """
    Send a templated HTML email with plain text fallback.
    
    Args:
        subject: Email subject
        template_name: Path to HTML template (e.g., 'emails/welcome.html')
        context: Dictionary of template variables
        recipient_list: List of recipient emails
        from_email: Sender email (defaults to settings.DEFAULT_FROM_EMAIL)
        fail_silently: If True, suppress exceptions
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        # Render HTML version
        html_message = render_to_string(template_name, context)
        
        # Generate plain text version (strip HTML tags)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=recipient_list if isinstance(recipient_list, list) else [recipient_list],
            html_message=html_message,
            fail_silently=fail_silently,
        )
        
        logger.info(f"Email sent: '{subject}' to {recipient_list}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email '{subject}' to {recipient_list}: {e}")
        if not fail_silently:
            raise
        return False


def get_base_context(user):
    """Build common context variables for all emails"""
    return {
        'user': user,
        'site_name': 'LuminaWealthAI',
        'support_url': 'mailto:support@luminawealthai.com',
        'dashboard_url': f'{settings.SITE_URL}/user/dashboard/',
        'strategies_url': f'{settings.SITE_URL}/user/strategies/',
        'transactions_url': f'{settings.SITE_URL}/user/transactions/',
        'profile_url': f'{settings.SITE_URL}/user/profile/',
    }


# ============================================
# SPECIFIC EMAIL SENDERS
# ============================================

def send_welcome_email(user, verify_url):
    """Send welcome email after registration"""
    context = get_base_context(user)
    context['verify_url'] = verify_url
    
    return send_templated_email(
        subject=f"Welcome to LuminaWealthAI, {user.first_name}! 🎉",
        template_name='emails/welcome.html',
        context=context,
        recipient_list=[user.email],
    )


def send_verification_email(user, verify_url):
    """Send email verification link"""
    context = get_base_context(user)
    context['verify_url'] = verify_url
    
    return send_templated_email(
        subject="Verify your LuminaWealthAI email address",
        template_name='emails/verify_email.html',
        context=context,
        recipient_list=[user.email],
    )


def send_password_reset_email(user, reset_url):
    """Send password reset link"""
    context = get_base_context(user)
    context['reset_url'] = reset_url
    
    return send_templated_email(
        subject="Reset your LuminaWealthAI password",
        template_name='emails/password_reset.html',
        context=context,
        recipient_list=[user.email],
    )


def send_kyc_approved_email(user):
    """Send KYC approval notification"""
    context = get_base_context(user)
    
    return send_templated_email(
        subject="✅ Your KYC Verification has been Approved!",
        template_name='emails/kyc_approved.html',
        context=context,
        recipient_list=[user.email],
    )


def send_kyc_rejected_email(user, rejection_reason):
    """Send KYC rejection notification with reason"""
    context = get_base_context(user)
    context['rejection_reason'] = rejection_reason
    context['kyc_url'] = f"{settings.SITE_URL}/user/kyc/"
    
    return send_templated_email(
        subject="⚠️ KYC Verification Action Required",
        template_name='emails/kyc_rejected.html',
        context=context,
        recipient_list=[user.email],
    )


def send_deposit_approved_email(user, deposit):
    """Send deposit approval notification"""
    context = get_base_context(user)
    context['deposit'] = deposit
    context['deposit_url'] = f"{settings.SITE_URL}/user/deposit/"
    
    return send_templated_email(
        subject=f"💰 Your Deposit of ${deposit.amount:.2f} has been Confirmed!",
        template_name='emails/deposit_approved.html',
        context=context,
        recipient_list=[user.email],
    )


def send_deposit_rejected_email(user, deposit):
    """Send deposit rejection notification"""
    context = get_base_context(user)
    context['deposit'] = deposit
    context['deposit_url'] = f"{settings.SITE_URL}/user/deposit/"
    
    return send_templated_email(
        subject=f"❌ Your Deposit Request Could Not Be Processed",
        template_name='emails/deposit_rejected.html',
        context=context,
        recipient_list=[user.email],
    )


def send_withdrawal_approved_email(user, withdrawal):
    """Send withdrawal approval notification"""
    context = get_base_context(user)
    context['withdrawal'] = withdrawal
    
    return send_templated_email(
        subject=f"💸 Your Withdrawal of ${withdrawal.amount:.2f} has been Processed!",
        template_name='emails/withdrawal_approved.html',
        context=context,
        recipient_list=[user.email],
    )


def send_withdrawal_rejected_email(user, withdrawal):
    """Send withdrawal rejection notification"""
    context = get_base_context(user)
    context['withdrawal'] = withdrawal
    context['withdraw_url'] = f"{settings.SITE_URL}/user/withdraw/"
    
    return send_templated_email(
        subject=f"❌ Your Withdrawal Request Could Not Be Processed",
        template_name='emails/withdrawal_rejected.html',
        context=context,
        recipient_list=[user.email],
    )