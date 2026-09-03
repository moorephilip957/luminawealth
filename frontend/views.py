from django.shortcuts import render

def home_view(request):
    return render(request, 'frontend/index.html')

def about_view(request):
    return render(request, 'frontend/about.html')

def features_view(request):
    return render(request, 'frontend/features.html')

def contact_view(request):
    return render(request, 'frontend/contact.html')

def faq_view(request):
    return render(request, 'frontend/faq.html')

def strategies_view(request):
    return render(request, 'frontend/strategies.html')

def terms_view(request):
    return render(request, 'frontend/terms.html')

def privacy_view(request):
    return render(request, 'frontend/privacy.html')
