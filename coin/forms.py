from django import forms
from .models import Strategy, SpinRecord


class StrategyForm(forms.ModelForm):
    """
    Form for creating and editing strategies.
    All fields are editable - no restrictions.
    """
    
    class Meta:
        model = Strategy
        fields = [
            'name', 'description', 'short_description',
            'invested_coin', 'strategy_type',
            'current_price', 'min_investment', 'management_fee',
            'risk_level', 'ai_accuracy', 'min_holding_period',
            'status', 'is_featured', 'is_public'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'placeholder': 'e.g., Conservative BTC Bot'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'rows': 4,
                'placeholder': 'Detailed description of the strategy...'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'placeholder': 'Short tagline (max 200 chars)'
            }),
            'invested_coin': forms.Select(attrs={
                'class': 'form-select bg-transparent border-secondary text-light'
            }),
            'strategy_type': forms.TextInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'placeholder': 'e.g., DCA, Momentum, Yield Farming'
            }),
            'current_price': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'placeholder': '100.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'min_investment': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'placeholder': '100.00',
                'step': '0.01',
                'min': '1'
            }),
            'management_fee': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'placeholder': '1.5',
                'step': '0.1',
                'min': '0'
            }),
            'risk_level': forms.Select(attrs={
                'class': 'form-select bg-transparent border-secondary text-light'
            }),
            'ai_accuracy': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'placeholder': '94.7',
                'step': '0.1',
                'min': '0',
                'max': '100'
            }),
            'min_holding_period': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'placeholder': '6',
                'min': '0'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select bg-transparent border-secondary text-light'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_current_price(self):
        price = self.cleaned_data.get('current_price')
        if price and price <= 0:
            raise forms.ValidationError('Price must be greater than 0.')
        return price
    
    def clean_ai_accuracy(self):
        accuracy = self.cleaned_data.get('ai_accuracy')
        if accuracy and (accuracy < 0 or accuracy > 100):
            raise forms.ValidationError('AI accuracy must be between 0 and 100.')
        return accuracy


class SpinForm(forms.Form):
    """
    Form for spinning up or down a strategy price.
    """
    amount = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg bg-transparent border-secondary text-light fs-4 fw-bold',
            'placeholder': '50.00',
            'step': '0.01',
            'min': '0.01'
        }),
        label='Amount'
    )
    
    reason = forms.CharField(
        required=False,  # Required for spin down, optional for spin up
        widget=forms.Textarea(attrs={
            'class': 'form-control bg-transparent border-secondary text-light',
            'rows': 2,
            'placeholder': 'e.g., Market rally, positive news...'
        }),
        label='Reason'
    )
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError('Amount must be greater than 0.')
        return amount