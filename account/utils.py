from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_verification_email(user, verification_url):
    """
    Send email verification email to user.
    
    Args:
        user: User object
        verification_url: Full URL for email verification
    """
    subject = 'Verify Your Email Address - LuminaWealthAI'
    
    # Render HTML template
    html_message = render_to_string('account/emails/email_verification.html', {
        'user': user,
        'verification_url': verification_url,
    })
    
    # Create plain text version
    plain_message = strip_tags(html_message)
    
    # Send email
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
    
    return True


def send_welcome_email(user, dashboard_url):
    """
    Send welcome email after email verification.
    
    Args:
        user: User object
        dashboard_url: URL to the user's dashboard
    """
    subject = 'Welcome to LuminaWealthAI! 🎉'
    
    html_message = render_to_string('account/emails/welcome.html', {
        'user': user,
        'dashboard_url': dashboard_url,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
    
    return True