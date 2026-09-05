from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminUserEditForm(forms.ModelForm):
    """
    Form for admins to edit user information.
    Allows editing of profile, verification, and account status.
    """
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'email_verified', 'kyc_status', 'kyc_rejection_reason',
            'is_active', 'timezone', 'preferred_currency',
            'balance', 'is_staff',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'placeholder': '+1 (555) 123-4567'
            }),
            'kyc_rejection_reason': forms.Textarea(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'rows': 3,
                'placeholder': 'Reason for KYC rejection...'
            }),
            'timezone': forms.TextInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
            }),
            'preferred_currency': forms.TextInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
            }),
            'balance': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'step': '0.01',
            }),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'email_verified': 'Email Verified',
            'kyc_status': 'KYC Status',
            'kyc_rejection_reason': 'KYC Rejection Reason',
            'is_active': 'Account Active',
            'timezone': 'Timezone',
            'preferred_currency': 'Preferred Currency',
            'balance': 'Available Balance (USD)',
            'is_staff': 'Admin Access',
        }