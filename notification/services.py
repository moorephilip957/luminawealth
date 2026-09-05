"""
Centralized notification service.
Creates notifications and optionally sends emails for important events.
"""
from django.conf import settings
from .models import Notification


def notify_kyc_approved(user, admin_user=None):
    """Notify user that KYC has been approved"""
    Notification.create_notification(
        user=user,
        title='✅ KYC Verification Approved',
        message=(
            f'Congratulations! Your identity verification has been approved. '
            f'You now have full access to all platform features including higher limits and premium strategies.'
        ),
        notification_type=Notification.TYPE_SUCCESS,
        category=Notification.CATEGORY_KYC,
        related_url='/user/kyc/'
    )
    
    # Also send email
    # try:
    #     from emails.email_utils import send_kyc_approved_email
    #     send_kyc_approved_email(user)
    # except Exception as e:
    #     print(f"Failed to send KYC approval email: {e}")


def notify_kyc_rejected(user, rejection_reason, admin_user=None):
    """Notify user that KYC has been rejected"""
    Notification.create_notification(
        user=user,
        title='⚠️ KYC Verification Needs Attention',
        message=(
            f'Your KYC submission requires updates. Reason: {rejection_reason}. '
            f'Please review the requirements and resubmit your documents.'
        ),
        notification_type=Notification.TYPE_WARNING,
        category=Notification.CATEGORY_KYC,
        related_url='/user/kyc/'
    )
    
    # Also send email
    # try:
    #     from emails.utils import send_kyc_rejected_email
    #     send_kyc_rejected_email(user, rejection_reason)
    # except Exception as e:
    #     print(f"Failed to send KYC rejection email: {e}")


def notify_deposit_approved(user, deposit, admin_user=None):
    """Notify user that deposit has been approved"""
    Notification.create_notification(
        user=user,
        title=f'💰 Deposit of ${deposit.amount:.2f} Confirmed',
        message=(
            f'Your deposit of ${deposit.amount:.2f} via {deposit.get_payment_method_display()} '
            f'has been successfully processed and credited to your account. '
            f'Your new balance is ${user.balance:.2f}.'
        ),
        notification_type=Notification.TYPE_SUCCESS,
        category=Notification.CATEGORY_DEPOSIT,
        related_url='/user/transactions/'
    )
    
    # Also send email
    # try:
    #     from emails.utils import send_deposit_approved_email
    #     send_deposit_approved_email(user, deposit)
    # except Exception as e:
    #     print(f"Failed to send deposit approval email: {e}")


def notify_deposit_rejected(user, deposit, reason, admin_user=None):
    """Notify user that deposit has been rejected"""
    Notification.create_notification(
        user=user,
        title=f'❌ Deposit Request Not Processed',
        message=(
            f'Your deposit request of ${deposit.amount:.2f} via {deposit.get_payment_method_display()} '
            f'could not be processed. Reason: {reason}. '
            f'Please review and submit a new request.'
        ),
        notification_type=Notification.TYPE_ERROR,
        category=Notification.CATEGORY_DEPOSIT,
        related_url='/user/deposit/'
    )
    
    # Also send email
    # try:
    #     from emails.utils import send_deposit_rejected_email
    #     send_deposit_rejected_email(user, deposit)
    # except Exception as e:
    #     print(f"Failed to send deposit rejection email: {e}")


def notify_deposit_submitted(user, deposit):
    """Notify user that deposit request was submitted (pending review)"""
    Notification.create_notification(
        user=user,
        title=f'📥 Deposit Request Received',
        message=(
            f'Your deposit request of ${deposit.amount:.2f} via {deposit.get_payment_method_display()} '
            f'has been received and is pending admin review. '
            f'You\'ll be notified once it\'s processed.'
        ),
        notification_type=Notification.TYPE_INFO,
        category=Notification.CATEGORY_DEPOSIT,
        related_url='/user/transactions/'
    )


def notify_withdrawal_approved(user, withdrawal, admin_user=None):
    """Notify user that withdrawal has been approved"""
    Notification.create_notification(
        user=user,
        title=f'💸 Withdrawal of ${withdrawal.amount:.2f} Processed',
        message=(
            f'Your withdrawal of ${withdrawal.amount:.2f} has been processed successfully. '
            f'You\'ll receive ${withdrawal.amount_after_fee:.2f} after network fees. '
            f'Funds are on their way to your destination.'
        ),
        notification_type=Notification.TYPE_SUCCESS,
        category=Notification.CATEGORY_WITHDRAWAL,
        related_url='/user/transactions/'
    )
    
    # Also send email
    # try:
    #     from emails.utils import send_withdrawal_approved_email
    #     send_withdrawal_approved_email(user, withdrawal)
    # except Exception as e:
    #     print(f"Failed to send withdrawal approval email: {e}")


def notify_withdrawal_rejected(user, withdrawal, reason, admin_user=None):
    """Notify user that withdrawal has been rejected"""
    Notification.create_notification(
        user=user,
        title=f'❌ Withdrawal Request Not Processed',
        message=(
            f'Your withdrawal request of ${withdrawal.amount:.2f} could not be processed. '
            f'Reason: {reason}. The funds remain safely in your account.'
        ),
        notification_type=Notification.TYPE_ERROR,
        category=Notification.CATEGORY_WITHDRAWAL,
        related_url='/user/withdraw/'
    )
    
    # Also send email
    # try:
    #     from emails.utils import send_withdrawal_rejected_email
    #     send_withdrawal_rejected_email(user, withdrawal)
    # except Exception as e:
    #     print(f"Failed to send withdrawal rejection email: {e}")


def notify_withdrawal_submitted(user, withdrawal):
    """Notify user that withdrawal request was submitted"""
    Notification.create_notification(
        user=user,
        title=f'📤 Withdrawal Request Received',
        message=(
            f'Your withdrawal request of ${withdrawal.amount:.2f} has been received '
            f'and is pending admin review. You\'ll be notified once it\'s processed.'
        ),
        notification_type=Notification.TYPE_INFO,
        category=Notification.CATEGORY_WITHDRAWAL,
        related_url='/user/transactions/'
    )


def notify_investment_made(user, strategy, amount):
    """Notify user that they've made an investment"""
    Notification.create_notification(
        user=user,
        title=f'📈 Investment Successful',
        message=(
            f'You\'ve successfully invested ${amount:.2f} in the {strategy.name} strategy. '
            f'Your investment is now active and being managed by our AI algorithms.'
        ),
        notification_type=Notification.TYPE_SUCCESS,
        category=Notification.CATEGORY_STRATEGY,
        related_url=f'/user/strategies/{strategy.id}/'
    )


def notify_investment_liquidated(user, strategy, amount, profit):
    """Notify user that they've liquidated an investment"""
    profit_word = 'profit' if profit >= 0 else 'loss'
    Notification.create_notification(
        user=user,
        title=f'💼 Investment Liquidated',
        message=(
            f'Your position in {strategy.name} has been liquidated. '
            f'${amount:.2f} has been returned to your available balance. '
            f'Total {profit_word}: ${abs(profit):.2f}.'
        ),
        notification_type=Notification.TYPE_INFO if profit >= 0 else Notification.TYPE_WARNING,
        category=Notification.CATEGORY_STRATEGY,
        related_url='/user/portfolio/'
    )


def notify_account_suspended(user, reason, admin_user=None):
    """Notify user that their account has been suspended"""
    Notification.create_notification(
        user=user,
        title='🚫 Account Suspended',
        message=(
            f'Your account has been suspended. Reason: {reason}. '
            f'Please contact support for more information.'
        ),
        notification_type=Notification.TYPE_ERROR,
        category=Notification.CATEGORY_SECURITY,
        related_url='/user/account-suspended/'
    )


def notify_account_reactivated(user, admin_user=None):
    """Notify user that their account has been reactivated"""
    Notification.create_notification(
        user=user,
        title='✅ Account Reactivated',
        message=(
            f'Your account has been reactivated. '
            f'You now have full access to all platform features again.'
        ),
        notification_type=Notification.TYPE_SUCCESS,
        category=Notification.CATEGORY_SECURITY,
        related_url='/user/dashboard/'
    )


def notify_password_changed(user):
    """Notify user that their password was changed"""
    Notification.create_notification(
        user=user,
        title='🔐 Password Changed',
        message=(
            f'Your password has been successfully changed. '
            f'If you didn\'t make this change, please contact support immediately.'
        ),
        notification_type=Notification.TYPE_INFO,
        category=Notification.CATEGORY_SECURITY,
        related_url='/user/profile/settings/'
    )


def notify_new_login(user, device_info, ip_address):
    """Notify user of a new login from a new device"""
    Notification.create_notification(
        user=user,
        title='🖥️ New Device Login',
        message=(
            f'A new login was detected from {device_info} (IP: {ip_address}). '
            f'If this wasn\'t you, please change your password immediately.'
        ),
        notification_type=Notification.TYPE_WARNING,
        category=Notification.CATEGORY_SECURITY,
        related_url='/user/profile/'
    )


def notify_admin_fund_action(target_user, action, amount, admin_user):
    """Notify user that admin has deposited/withdrawn funds"""
    if action == 'deposit':
        title = f'💰 Funds Added to Your Account'
        message = (
            f'${amount:.2f} has been credited to your account by our support team. '
            f'Your new balance is ${target_user.balance:.2f}.'
        )
        notif_type = Notification.TYPE_SUCCESS
    else:
        title = f'💸 Funds Deducted from Your Account'
        message = (
            f'${amount:.2f} has been debited from your account by our support team. '
            f'Your new balance is ${target_user.balance:.2f}.'
        )
        notif_type = Notification.TYPE_INFO
    
    Notification.create_notification(
        user=target_user,
        title=title,
        message=message,
        notification_type=notif_type,
        category=Notification.CATEGORY_SYSTEM,
        related_url='/user/transactions/'
    )