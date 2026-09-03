from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re

User = get_user_model()


class RegistrationForm(forms.ModelForm):
    """
    Registration form for new users.
    Includes password confirmation and validation.
    """
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Create password',
            'id': 'registerPassword',
            'oninput': 'checkPasswordStrength(this.value)'
        }),
        help_text="Password must be at least 8 characters with uppercase, lowercase, and number."
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Confirm password',
            'id': 'confirmPassword'
        }),
        label="Confirm Password"
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'auth-input',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'auth-input',
                'placeholder': 'Phone number (optional)'
            }),
        }
    
    def clean_email(self):
        """Validate email is unique and properly formatted"""
        email = self.cleaned_data.get('email', '').lower().strip()
        
        if User.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        
        return email
    
    def clean_phone(self):
        """Validate phone number format if provided"""
        phone = self.cleaned_data.get('phone', '').strip()
        
        if phone:
            # Remove all non-digit characters except +
            phone_clean = re.sub(r'[^\d+]', '', phone)
            
            # Basic validation: should have at least 10 digits
            digits_only = re.sub(r'\D', '', phone_clean)
            if len(digits_only) < 10:
                raise ValidationError('Phone number must have at least 10 digits.')
            
            return phone_clean
        
        return phone
    
    def clean(self):
        """Validate passwords match and meet requirements"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', 'Passwords do not match.')
            
            # Password strength validation
            if len(password) < 8:
                self.add_error('password', 'Password must be at least 8 characters long.')
            
            if not re.search(r'[A-Z]', password):
                self.add_error('password', 'Password must contain at least one uppercase letter.')
            
            if not re.search(r'[a-z]', password):
                self.add_error('password', 'Password must contain at least one lowercase letter.')
            
            if not re.search(r'\d', password):
                self.add_error('password', 'Password must contain at least one number.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save user with hashed password and set username to email"""
        user = super().save(commit=False)
        
        # Set username to email (since we're using email for login)
        user.username = user.email
        
        # Set password with hashing
        user.set_password(self.cleaned_data['password'])
        
        # User is active but email not verified yet
        user.is_active = True
        user.email_verified = False
        
        if commit:
            user.save()
        
        return user