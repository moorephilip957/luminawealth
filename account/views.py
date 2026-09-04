from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from .forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from .utils import send_verification_email, send_welcome_email, send_otp_email, send_password_reset_email

from .models import User, OTP, TrustedDevice

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
        return redirect('account:login')
    
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


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def login_view(request):
    """
    Handle user login with smart OTP logic.
    
    Flow:
    1. User submits email + password
    2. Validate credentials
    3. Check if device is trusted (via cookie)
    4. If trusted: log in directly → dashboard
    5. If not trusted: send OTP → OTP page
    """
    
    # If already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('customer:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            user = form.cleaned_data['user']
            remember_device = form.cleaned_data.get('remember_device', False)
            
            # Get device info
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            device_name = TrustedDevice.get_friendly_device_name(user_agent)
            
            # Check if device is trusted (via cookie)
            device_token = request.COOKIES.get(settings.TRUSTED_DEVICE_COOKIE_NAME)
            trusted_device = None
            
            if device_token:
                trusted_device = TrustedDevice.get_device_by_token(device_token)
                
                # Verify it belongs to this user and is valid
                if trusted_device and trusted_device.user != user:
                    trusted_device = None
                
                if trusted_device and not trusted_device.is_valid():
                    trusted_device = None
            
            # If device is trusted, skip OTP
            if trusted_device:
                # Update last used and extend expiry
                trusted_device.update_last_used(ip_address=ip_address)
                trusted_device.extend_expiry()
                
                # Log the user in
                auth_login(request, user)
                
                messages.success(
                    request,
                    f'Welcome back, {user.first_name}! 🎉'
                )
                
                # Redirect to dashboard or next page
                next_url = request.GET.get('next', 'customer:dashboard')
                return redirect(next_url)
            
            # Device not trusted - need OTP
            # Check rate limiting (don't spam OTPs)
            if OTP.has_recent_otp(user, minutes=settings.OTP_RATE_LIMIT_MINUTES):
                messages.warning(
                    request,
                    'An OTP was recently sent to your email. Please check your inbox '
                    'or wait a minute before requesting a new one.'
                )
                return redirect('account:login')
            
            # Create new OTP
            otp = OTP.create_otp(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Send OTP email
            try:
                # Try to get location from IP (simplified - use IP as location for demo)
                location = f"IP: {ip_address}"
                
                send_otp_email(
                    user=user,
                    otp_code=otp.code,
                    device_name=device_name,
                    location=location,
                    request=request
                )
                
                # Store user info in session for OTP verification
                request.session['pending_login_user_id'] = user.id
                request.session['pending_login_remember_device'] = remember_device
                request.session['pending_login_ip'] = ip_address
                request.session['pending_login_user_agent'] = user_agent
                request.session['otp_attempts'] = 0
                
                messages.info(
                    request,
                    f'We sent a 6-digit verification code to {user.email}. '
                    f'The code expires in 10 minutes.'
                )
                
                # Redirect to OTP verification page
                return redirect('account:otp_verify')
                
            except Exception as e:
                messages.error(
                    request,
                    'Failed to send verification code. Please try again later.'
                )
                print(f"OTP email failed: {e}")
        else:
            # Form has errors - display them
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        # GET request - show empty form
        form = LoginForm()
    
    return render(request, 'account/login.html', {
        'form': form,
        'page_title': 'Sign In'
    })


def otp_verify_view(request):
    """
    Handle OTP verification during login.
    
    Flow:
    1. Check session for pending login
    2. Validate 6-digit code
    3. On success: complete login, optionally save trusted device
    4. On failure: increment attempts, lock after 3 failures
    """
    
    # Check if there's a pending login in session
    pending_user_id = request.session.get('pending_login_user_id')
    
    if not pending_user_id:
        # No pending login - redirect to login page
        messages.warning(request, 'Please log in first to verify your identity.')
        return redirect('account:login')
    
    # Get the user
    try:
        user = User.objects.get(id=pending_user_id)
    except User.DoesNotExist:
        # User doesn't exist anymore - clear session
        _clear_otp_session(request)
        messages.error(request, 'Account not found. Please try logging in again.')
        return redirect('account:login')
    
    # Get active OTP for this user
    active_otp = OTP.get_active_otp(user)
    
    if not active_otp:
        # No active OTP - need to resend
        _clear_otp_session(request)
        messages.warning(
            request,
            'Your verification code has expired. Please log in again to receive a new code.'
        )
        return redirect('account:login')
    
    # Calculate time remaining for display
    time_remaining = active_otp.expires_at - timezone.now()
    minutes_remaining = max(0, int(time_remaining.total_seconds() / 60))
    seconds_remaining = max(0, int(time_remaining.total_seconds() % 60))
    
    # Get attempt count
    otp_attempts = request.session.get('otp_attempts', 0)
    attempts_remaining = 3 - otp_attempts
    
    if request.method == 'POST':
        # Get the OTP code from form
        otp_code = ''.join([
            request.POST.get(f'otp_{i}', '') for i in range(6)
        ])
        
        # Validate code format
        if len(otp_code) != 6 or not otp_code.isdigit():
            messages.error(request, 'Please enter a valid 6-digit code.')
            return render(request, 'account/otp.html', {
                'user_email': _mask_email(user.email),
                'time_remaining': f"{minutes_remaining}:{seconds_remaining:02d}",
                'attempts_remaining': attempts_remaining,
            })
        
        # Check if too many attempts
        if otp_attempts >= 3:
            _clear_otp_session(request)
            messages.error(
                request,
                'Too many incorrect attempts. Please log in again to receive a new code.'
            )
            return redirect('account:login')
        
        # Verify the OTP
        if active_otp.verify(otp_code):
            # ✅ OTP is valid - complete the login!
            
            # Log the user in
            auth_login(request, user)
            
            # Check if user wants to remember this device
            remember_device = request.session.get('pending_login_remember_device', False)
            
            if remember_device:
                # Create trusted device
                ip_address = request.session.get('pending_login_ip')
                user_agent = request.session.get('pending_login_user_agent', '')
                device_name = TrustedDevice.get_friendly_device_name(user_agent)
                
                trusted_device = TrustedDevice.create_trusted_device(
                    user=user,
                    device_name=device_name,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                # Set cookie with device token
                response = redirect('customer:dashboard')
                response.set_cookie(
                    key=settings.TRUSTED_DEVICE_COOKIE_NAME,
                    value=trusted_device.device_token,
                    max_age=settings.TRUSTED_DEVICE_COOKIE_AGE,
                    httponly=settings.TRUSTED_DEVICE_COOKIE_HTTPONLY,
                    secure=settings.TRUSTED_DEVICE_COOKIE_SECURE,
                    samesite='Lax'
                )
                
                messages.success(
                    request,
                    f'Welcome back, {user.first_name}! 🎉 This device is now trusted for 30 days.'
                )
            else:
                response = redirect('customer:dashboard')
                messages.success(
                    request,
                    f'Welcome back, {user.first_name}! 🎉'
                )
            
            # Clear OTP session data
            _clear_otp_session(request)
            
            # Redirect to dashboard or next page
            next_url = request.GET.get('next', 'customer:dashboard')
            return redirect(next_url)
        
        else:
            # ❌ OTP is invalid
            otp_attempts += 1
            request.session['otp_attempts'] = otp_attempts
            attempts_remaining = 3 - otp_attempts
            
            if attempts_remaining <= 0:
                # Too many failed attempts
                _clear_otp_session(request)
                messages.error(
                    request,
                    'Too many incorrect attempts. Please log in again to receive a new code.'
                )
                return redirect('account:login')
            else:
                messages.error(
                    request,
                    f'Invalid code. You have {attempts_remaining} attempt(s) remaining.'
                )
    
    # GET request or invalid POST - show OTP form
    return render(request, 'account/otp.html', {
        'user_email': _mask_email(user.email),
        'time_remaining': f"{minutes_remaining}:{seconds_remaining:02d}",
        'attempts_remaining': attempts_remaining,
    })


def resend_otp_view(request):
    """
    Handle resend OTP requests during login.
    Creates a new OTP and sends it via email.
    """
    
    # Check if there's a pending login in session
    pending_user_id = request.session.get('pending_login_user_id')
    
    if not pending_user_id:
        messages.warning(request, 'Please log in first to verify your identity.')
        return redirect('login')
    
    # Get the user
    try:
        user = User.objects.get(id=pending_user_id)
    except User.DoesNotExist:
        _clear_otp_session(request)
        messages.error(request, 'Account not found. Please try logging in again.')
        return redirect('account:login')
    
    # Check rate limiting
    if OTP.has_recent_otp(user, minutes=settings.OTP_RATE_LIMIT_MINUTES):
        messages.warning(
            request,
            'Please wait a moment before requesting a new code.'
        )
        return redirect('account:otp_verify')
    
    # Get device info from session
    ip_address = request.session.get('pending_login_ip')
    user_agent = request.session.get('pending_login_user_agent', '')
    device_name = TrustedDevice.get_friendly_device_name(user_agent)
    
    # Create new OTP (this automatically invalidates any existing ones)
    otp = OTP.create_otp(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Send OTP email
    try:
        location = f"IP: {ip_address}"
        
        send_otp_email(
            user=user,
            otp_code=otp.code,
            device_name=device_name,
            location=location,
            request=request
        )
        
        # Reset attempt counter
        request.session['otp_attempts'] = 0
        
        messages.success(
            request,
            f'A new verification code has been sent to {_mask_email(user.email)}.'
        )
        
    except Exception as e:
        messages.error(request, 'Failed to send verification code. Please try again later.')
        print(f"Resend OTP email failed: {e}")
    
    return redirect('account:otp_verify')


def _clear_otp_session(request):
    """Helper function to clear OTP-related session data"""
    keys_to_remove = [
        'pending_login_user_id',
        'pending_login_remember_device',
        'pending_login_ip',
        'pending_login_user_agent',
        'otp_attempts',
    ]
    for key in keys_to_remove:
        request.session.pop(key, None)


def _mask_email(email):
    """
    Mask email for display (e.g., j***@example.com)
    """
    if not email or '@' not in email:
        return email
    
    local_part, domain = email.split('@', 1)
    
    if len(local_part) <= 2:
        masked_local = local_part[0] + '***'
    else:
        masked_local = local_part[0] + '***'
    
    return f"{masked_local}@{domain}"


def logout_view(request):
    """
    Handle user logout.
    Clears session but keeps trusted device cookie.
    """
    
    # Get user before logout for message
    user_name = request.user.first_name if request.user.is_authenticated else ''
    
    # Logout user
    auth_logout(request)
    
    # Note: We DON'T delete the trusted device cookie
    # This way, when they log in again from the same device, they skip OTP
    
    if user_name:
        messages.success(request, f'You have been logged out, {user_name}. See you soon! 👋')
    else:
        messages.success(request, 'You have been logged out successfully.')
    
    return redirect('frontend:home')


def forgot_password_view(request):
    """
    Handle forgot password requests.
    Sends reset email if account exists.
    """
    
    # If user is logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('customer:dashboard')
    
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Generate reset token
                token = user.generate_password_reset_token()
                
                # Build reset URL
                reset_url = request.build_absolute_uri(
                    reverse('account:reset_password', kwargs={'token': token})
                )
                
                # Send email
                send_password_reset_email(user, reset_url, request)
                
            except User.DoesNotExist:
                # Don't reveal if email exists (security)
                pass
            
            # Always show same message (security)
            messages.success(
                request,
                f'If an account exists with {email}, you will receive a password reset link shortly. '
                f'The link expires in 1 hour.'
            )
            
            return redirect('account:login')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'account/forgot_password.html', {
        'form': form,
        'page_title': 'Forgot Password'
    })


def reset_password_view(request, token):
    """
    Handle password reset when user clicks the link in email.
    """
    
    # Find user with this token
    try:
        user = User.objects.get(password_reset_token=token)
    except User.DoesNotExist:
        return render(request, 'account/reset_password_result.html', {
            'status': 'invalid',
            'title': 'Invalid Reset Link',
            'message': 'This password reset link is invalid or has already been used.',
            'icon': 'bi-x-circle-fill',
            'icon_color': 'danger',
        })
    
    # Check if token is expired
    if not user.is_password_reset_token_valid():
        return render(request, 'account/reset_password_result.html', {
            'status': 'expired',
            'title': 'Reset Link Expired',
            'message': 'This password reset link has expired. Reset links are valid for 1 hour.',
            'icon': 'bi-clock-fill',
            'icon_color': 'warning',
        })
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            
            # Set new password
            user.set_password(new_password)
            
            # Clear reset token
            user.clear_password_reset_token()
            
            # Invalidate all sessions for security
            user.invalidate_all_sessions()
            
            # Save user
            user.save()
            
            return render(request, 'account/reset_password_result.html', {
                'status': 'success',
                'title': 'Password Reset Successfully!',
                'message': 'Your password has been reset. All other devices have been logged out for security. You can now log in with your new password.',
                'icon': 'bi-check-circle-fill',
                'icon_color': 'success',
            })
    else:
        form = ResetPasswordForm()
    
    return render(request, 'account/reset_password.html', {
        'form': form,
        'token': token,
        'user_email': _mask_email(user.email),
        'page_title': 'Reset Password'
    })
