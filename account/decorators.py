from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def email_verified_required(view_func):
    """
    Decorator that checks if user's email is verified.
    Redirects to a verification prompt page if not verified.
    
    Usage:
        @email_verified_required
        def deposit_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.email_verified:
            messages.warning(
                request,
                'Please verify your email address to access this feature. '
                'Check your inbox for the verification link.'
            )
            # Store the original URL to redirect back after verification
            request.session['email_verification_next'] = request.get_full_path()
            return redirect('email_verification_prompt')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def kyc_required(view_func):
    """
    Decorator that checks if user has completed KYC verification.
    Redirects to KYC page if not verified.
    
    Usage:
        @kyc_required
        def withdraw_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check KYC status
        from .models import User
        
        if request.user.kyc_status == User.KYC_NOT_STARTED:
            messages.info(
                request,
                'Please complete KYC verification to access withdrawals. '
                'This is required for security and regulatory compliance.'
            )
            request.session['kyc_next'] = request.get_full_path()
            return redirect('kyc')
        
        elif request.user.kyc_status == User.KYC_PENDING:
            messages.info(
                request,
                'Your KYC verification is currently under review. '
                'This usually takes 24-48 hours. We\'ll notify you once approved.'
            )
            return redirect('kyc_status')
        
        elif request.user.kyc_status == User.KYC_REJECTED:
            messages.error(
                request,
                f'Your KYC verification was rejected. '
                f'Reason: {request.user.kyc_rejection_reason or "Please review the requirements and resubmit."}'
            )
            request.session['kyc_next'] = request.get_full_path()
            return redirect('kyc')
        
        # KYC_APPROVED - allow access
        return view_func(request, *args, **kwargs)
    
    return wrapper


def email_and_kyc_required(view_func):
    """
    Decorator that checks both email verification and KYC.
    Useful for features that require both (e.g., high-value withdrawals).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check email first
        if not request.user.email_verified:
            messages.warning(
                request,
                'Please verify your email address first.'
            )
            request.session['email_verification_next'] = request.get_full_path()
            return redirect('email_verification_prompt')
        
        # Then check KYC
        from .models import User
        
        if request.user.kyc_status != User.KYC_APPROVED:
            messages.info(
                request,
                'Please complete KYC verification to access this feature.'
            )
            request.session['kyc_next'] = request.get_full_path()
            return redirect('kyc')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper