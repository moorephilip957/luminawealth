from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from .forms import RegistrationForm
from .utils import send_verification_email, send_welcome_email
from .models import User


def register_view(request):
    """
    Handle user registration.
    """
    
    if request.user.is_authenticated:
        return redirect('client_dashboard')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        
        if form.is_valid():
            # Save the user
            user = form.save()
            
            # DEBUG: Check user state after save
            print(f"\n=== REGISTRATION DEBUG ===")
            print(f"User created: {user.email}")
            print(f"User ID: {user.id}")
            print(f"Email verified before token: {user.email_verified}")
            
            # Generate email verification token
            token = user.generate_email_verification_token()
            
            # DEBUG: Check token was generated
            user.refresh_from_db()  # Refresh from database
            print(f"Token generated: {token}")
            print(f"Token in DB: {user.email_verification_token}")
            print(f"Token created at: {user.email_verification_token_created_at}")
            print(f"===========================\n")
            
            # Build verification URL
            verification_url = request.build_absolute_uri(
                reverse('account:verify_email', kwargs={'token': token})
            )
            
            print(f"Verification URL: {verification_url}")
            
            # Send verification email
            try:
                send_verification_email(user, verification_url)
                messages.success(
                    request,
                    f'Account created successfully! Please check your email ({user.email}) '
                    f'to verify your account. The verification link expires in 24 hours.'
                )
            except Exception as e:
                messages.warning(
                    request,
                    f'Account created successfully! However, we couldn\'t send the verification email. '
                    f'Please contact support or try again later.'
                )
                print(f"Email sending failed: {e}")
            
            return redirect('account:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = RegistrationForm()
    
    return render(request, 'account/register.html', {
        'form': form,
        'page_title': 'Create Account'
    })


def verify_email_view(request, token):
    """
    Handle email verification when user clicks the link in their email.
    """
    
    # Try to find user with this token
    try:
        user = User.objects.get(email_verification_token=token)
        
        # DEBUG: Print token info (remove in production)
        print(f"\n=== EMAIL VERIFICATION DEBUG ===")
        print(f"Token from URL: {token}")
        print(f"User found: {user.email}")
        print(f"Token in DB: {user.email_verification_token}")
        print(f"Token created at: {user.email_verification_token_created_at}")
        print(f"Current time: {timezone.now()}")
        if user.email_verification_token_created_at:
            token_age = timezone.now() - user.email_verification_token_created_at
            print(f"Token age: {token_age}")
            print(f"Token age in hours: {token_age.total_seconds() / 3600}")
        print(f"Email already verified: {user.email_verified}")
        print(f"================================\n")
        
    except User.DoesNotExist:
        # Token is invalid
        return render(request, 'account/email_verification_result.html', {
            'status': 'invalid',
            'title': 'Invalid Verification Link',
            'message': 'This verification link is invalid or has already been used.',
            'icon': 'bi-x-circle-fill',
            'icon_color': 'danger',
        })
    
    # Check if already verified
    if user.email_verified:
        return render(request, 'account/email_verification_result.html', {
            'status': 'already_verified',
            'title': 'Email Already Verified',
            'message': 'Your email has already been verified. You can now log in to your account.',
            'icon': 'bi-info-circle-fill',
            'icon_color': 'info',
        })
    
    # Check if token is expired or timestamp is missing
    if not user.email_verification_token_created_at:
        # Timestamp is missing - this shouldn't happen, but handle it gracefully
        # Regenerate token and ask user to request a new email
        user.generate_email_verification_token()
        return render(request, 'account/email_verification_result.html', {
            'status': 'expired',
            'title': 'Verification Link Invalid',
            'message': 'This verification link is invalid. Please request a new verification email.',
            'icon': 'bi-clock-fill',
            'icon_color': 'warning',
            'show_resend': True,
            'user_email': user.email,
        })
    
    # Check if token is expired (24 hours)
    token_age = timezone.now() - user.email_verification_token_created_at
    if token_age.total_seconds() > 86400:  # 24 hours in seconds
        return render(request, 'account/email_verification_result.html', {
            'status': 'expired',
            'title': 'Verification Link Expired',
            'message': 'This verification link has expired. Verification links are valid for 24 hours.',
            'icon': 'bi-clock-fill',
            'icon_color': 'warning',
            'show_resend': True,
            'user_email': user.email,
        })
    
    # All checks passed - verify the email
    user.verify_email()
    
    # Send welcome email
    try:
        dashboard_url = request.build_absolute_uri(reverse('client_dashboard'))
        send_welcome_email(user, dashboard_url)
    except Exception as e:
        print(f"Welcome email failed: {e}")
    
    # Show success page
    return render(request, 'account/email_verification_result.html', {
        'status': 'success',
        'title': 'Email Verified Successfully!',
        'message': f'Your email ({user.email}) has been verified. You can now log in and start using LuminaWealthAI.',
        'icon': 'bi-check-circle-fill',
        'icon_color': 'success',
        'user_name': user.first_name,
    })


def resend_verification_view(request):
    """
    Handle resend verification email requests.
    Can be accessed via POST from the expired verification page.
    """
    if request.method != 'POST':
        return redirect('account:ogin')
    
    email = request.POST.get('email', '').strip().lower()
    
    if not email:
        messages.error(request, 'Please provide your email address.')
        return redirect('account:login')
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if email exists (security)
        messages.info(
            request,
            'If an account exists with that email, a new verification link has been sent.'
        )
        return redirect('account:login')
    
    # Check if already verified
    if user.email_verified:
        messages.info(request, 'Your email is already verified. You can log in now.')
        return redirect('login')
    
    # Generate new token
    token = user.generate_email_verification_token()
    verification_url = request.build_absolute_uri(
        reverse('account:verify_email', kwargs={'token': token})
    )
    
    # Send email
    try:
        send_verification_email(user, verification_url)
        messages.success(
            request,
            f'A new verification link has been sent to {email}. Please check your inbox.'
        )
    except Exception as e:
        messages.error(request, 'Failed to send verification email. Please try again later.')
        print(f"Resend email failed: {e}")
    
    return redirect('account:login')


def login_view(request):
    return render(request, 'account/login.html')

def otp_view(request):
    return render(request, 'account/otp.html')
