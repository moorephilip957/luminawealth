from django.shortcuts import render
from .decorators import redirect_authenticated_users

@redirect_authenticated_users
def home_view(request):
    return render(request, 'frontend/index.html')

@redirect_authenticated_users
def about_view(request):
    return render(request, 'frontend/about.html')

@redirect_authenticated_users
def features_view(request):
    return render(request, 'frontend/features.html')

@redirect_authenticated_users
def contact_view(request):
    return render(request, 'frontend/contact.html')

@redirect_authenticated_users
def faq_view(request):
    return render(request, 'frontend/faq.html')

@redirect_authenticated_users
def strategies_view(request):
    return render(request, 'frontend/strategies.html')

@redirect_authenticated_users
def terms_view(request):
    return render(request, 'frontend/terms.html')

@redirect_authenticated_users
def privacy_view(request):
    return render(request, 'frontend/privacy.html')
