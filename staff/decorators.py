from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from functools import wraps


def account_active_required(view_func):
    """
    Decorator that checks if user account is active (not suspended).
    
    Flow:
    1. If not authenticated → redirect to login
    2. If authenticated but is_active=False → redirect to suspended page
    3. If authenticated and active → proceed to view
    
    Usage:
        @login_required
        @account_active_required
        def my_view(request):
            ...
    
    Or combine with login_required:
        @account_active_required  # This handles both auth and active checks
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Store the original URL to redirect back after login
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Check if account is active
        if not request.user.is_active:
            # Log them out to clear the session
            # (optional - some platforms keep them logged in to show the suspended page)
            # For now, we'll keep them logged in so they can see the suspension info
            
            messages.error(
                request,
                'Your account has been suspended. Please contact support for assistance.'
            )
            
            return redirect('account_suspended')
        
        # All checks passed - proceed to view
        return view_func(request, *args, **kwargs)
    
    return wrapper


# Alternative: Combined decorator that handles both auth and active checks
from functools import wraps
from django.shortcuts import redirect

def client_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 1. Not logged in? Go to login.
        if not request.user.is_authenticated:
            return redirect('account:login') # Adjust to your login namespace
        
        # 2. Logged in but suspended? Go to suspended page.
        if getattr(request.user, 'account_status', 'active') == 'suspended':
            return redirect('customer:account_suspended')
        
        # 3. All good, show the page.
        return view_func(request, *args, **kwargs)
    return wrapper