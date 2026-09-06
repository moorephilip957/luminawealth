from functools import wraps
from django.shortcuts import redirect


def redirect_authenticated_users(view_func):
    """
    Decorator that redirects authenticated users away from public pages.
    
    - Staff users → redirect to staff:dashboard
    - Regular users → redirect to customer:dashboard
    - Anonymous users → allowed to view the page
    
    Usage:
        @redirect_authenticated_users
        def home_view(request):
            return render(request, 'home.html')
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # If user is authenticated, redirect them to their dashboard
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect('staff:admin_users')
            else:
                return redirect('customer:dashboard')
        
        # Anonymous users can view the page
        return view_func(request, *args, **kwargs)
    
    return wrapper