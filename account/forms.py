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


class LoginForm(forms.Form):
    """
    Login form with email and password.
    Includes account lockout checking.
    """
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Email address',
            'autocomplete': 'email'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Password',
            'id': 'loginPassword',
            'autocomplete': 'current-password'
        })
    )
    
    remember_device = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'rememberDevice'
        })
    )
    
    def clean(self):
        """
        Validate credentials and check account status.
        Returns cleaned data with user object if valid.
        For suspended accounts, returns user with 'account_suspended' flag.
        """
        cleaned_data = super().clean()
        email = cleaned_data.get('email', '').lower().strip()
        password = cleaned_data.get('password')
        
        if not email or not password:
            return cleaned_data
        
        # Find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists (security)
            raise forms.ValidationError(
                'Invalid email or password. Please try again.'
            )
        
        # Verify password FIRST (security: only show suspension to legitimate users)
        if not user.check_password(password):
            # Record failed login attempt
            user.record_failed_login()
            raise forms.ValidationError(
                'Invalid email or password. Please try again.'
            )
        
        # Password is correct - now check account status
        # Check if account is locked (too many failed attempts)
        if user.is_account_locked():
            from django.utils import timezone
            time_remaining = user.account_locked_until - timezone.now()
            minutes = int(time_remaining.total_seconds() / 60) + 1
            raise forms.ValidationError(
                f'Too many failed login attempts. Your account is locked. '
                f'Please try again in {minutes} minute(s).'
            )
        
        # Check if account is suspended (is_active=False)
        if not user.is_active:
            # DON'T raise error - instead, store user with a flag
            # The view will redirect to the suspended page
            cleaned_data['user'] = user
            cleaned_data['account_suspended'] = True
            return cleaned_data
        
        # Account is active - reset failed attempts and proceed
        user.record_successful_login()
        cleaned_data['user'] = user
        cleaned_data['account_suspended'] = False
        
        return cleaned_data


class ForgotPasswordForm(forms.Form):
    """
    Form for requesting a password reset.
    Only requires email address.
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email'
        })
    )
    
    def clean_email(self):
        """Validate email exists in system"""
        email = self.cleaned_data.get('email', '').lower().strip()
        
        # We don't reveal if email exists (security)
        # Just return it - the view will handle the logic
        return email


class ResetPasswordForm(forms.Form):
    """
    Form for setting a new password after reset.
    """
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'New password',
            'id': 'newPassword'
        }),
        help_text="Password must be at least 8 characters with uppercase, lowercase, and number."
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'auth-input',
            'placeholder': 'Confirm new password',
            'id': 'confirmPassword'
        }),
        label="Confirm New Password"
    )
    
    def clean(self):
        """Validate passwords match and meet requirements"""
        cleaned_data = super().clean()
        password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', 'Passwords do not match.')
            
            # Password strength validation
            if len(password) < 8:
                self.add_error('new_password', 'Password must be at least 8 characters long.')
            
            if not re.search(r'[A-Z]', password):
                self.add_error('new_password', 'Password must contain at least one uppercase letter.')
            
            if not re.search(r'[a-z]', password):
                self.add_error('new_password', 'Password must contain at least one lowercase letter.')
            
            if not re.search(r'\d', password):
                self.add_error('new_password', 'Password must contain at least one number.')
        
        return cleaned_data