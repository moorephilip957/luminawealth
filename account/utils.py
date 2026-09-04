from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.utils import timezone


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


def send_otp_email(user, otp_code, device_name='Unknown Device', location='Unknown Location', request=None):
    """
    Send OTP email for login verification.
    
    Args:
        user: User object
        otp_code: 6-digit OTP code
        device_name: Friendly name of device (e.g., "Chrome on Windows")
        location: Geographic location (e.g., "New York, USA")
        request: Django request object (for building URLs)
    """
    subject = f'Your Login Code: {otp_code} - LuminaWealthAI'
    
    # Build security URL
    security_url = ''
    if request:
        from django.urls import reverse
        security_url = request.build_absolute_uri(reverse('customer:profile_settings'))
    
    # Render HTML template
    html_message = render_to_string('account/emails/otp_login.html', {
        'user': user,
        'otp_code': otp_code,
        'device_name': device_name,
        'location': location,
        'login_time': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
        'security_url': security_url,
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


def send_password_reset_email(user, reset_url, request=None):
    """
    Send password reset email to user.
    
    Args:
        user: User object
        reset_url: Full URL for password reset
        request: Django request object (for building security URL)
    """
    subject = 'Reset Your Password - LuminaWealthAI'
    
    # Build security URL
    security_url = ''
    if request:
        from django.urls import reverse
        security_url = request.build_absolute_uri(reverse('account:login'))
    
    # Render HTML template
    html_message = render_to_string('account/emails/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
        'security_url': security_url,
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