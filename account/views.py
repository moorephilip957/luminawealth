from django.shortcuts import render

def login_view(request):
    return render(request, 'account/login.html')

def register_view(request):
    return render(request, 'account/register.html')

def otp_view(request):
    return render(request, 'account/otp.html')
