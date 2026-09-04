from django import forms
from .models import Strategy


class StrategyForm(forms.ModelForm):
    """
    Form for creating and editing investment strategies.
    Admin can set any values without restrictions.
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
                'placeholder': 'Brief one-line description'
            }),
            'invested_coin': forms.Select(attrs={
                'class': 'form-select bg-transparent border-secondary text-light',
            }),
            'strategy_type': forms.TextInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'placeholder': 'e.g., DCA, Momentum, Yield Farming'
            }),
            'current_price': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '100.00'
            }),
            'min_investment': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'step': '0.01',
                'min': '1',
                'placeholder': '100.00'
            }),
            'management_fee': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '1.5'
            }),
            'risk_level': forms.Select(attrs={
                'class': 'form-select bg-transparent border-secondary text-light',
            }),
            'ai_accuracy': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '94.7'
            }),
            'min_holding_period': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'min': '0',
                'placeholder': '6'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select bg-transparent border-secondary text-light',
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'name': 'Strategy Name',
            'description': 'Full Description',
            'short_description': 'Short Description',
            'invested_coin': 'Invested Coin',
            'strategy_type': 'Strategy Type',
            'current_price': 'Initial Price (USD)',
            'min_investment': 'Minimum Investment (USD)',
            'management_fee': 'Management Fee (% per year)',
            'risk_level': 'Risk Level',
            'ai_accuracy': 'AI Accuracy (%)',
            'min_holding_period': 'Minimum Holding Period (months)',
            'status': 'Status',
            'is_featured': 'Featured Strategy',
            'is_public': 'Publicly Visible',
        }
        help_texts = {
            'name': 'Unique name for this strategy',
            'description': 'Detailed explanation of how this strategy works',
            'short_description': 'Brief tagline shown in strategy cards',
            'invested_coin': 'What asset this strategy primarily invests in',
            'strategy_type': 'Type of strategy (e.g., DCA, Momentum, Yield Farming)',
            'current_price': 'Starting price for this strategy',
            'min_investment': 'Minimum amount users can invest',
            'management_fee': 'Annual fee charged to investors (e.g., 1.5 for 1.5%)',
            'risk_level': 'Risk classification for this strategy',
            'ai_accuracy': 'Historical accuracy rate of the AI (0-100%)',
            'min_holding_period': 'Recommended minimum time to hold investment',
            'status': 'Active strategies are visible and investable',
            'is_featured': 'Show this strategy in featured section',
            'is_public': 'Make this strategy visible to all users',
        }


class StrategyEditForm(forms.ModelForm):
    """
    Form for editing existing investment strategies.
    Excludes current_price because price changes should ONLY happen via spin up/down.
    This maintains a clean audit trail through SpinRecord.
    """
    
    class Meta:
        model = Strategy
        fields = [
            'name', 'description', 'short_description',
            'invested_coin', 'strategy_type',
            'min_investment', 'management_fee',
            'risk_level', 'ai_accuracy', 'min_holding_period',
            'status', 'is_featured', 'is_public'
        ]
        # Same widgets, labels, and help_texts as StrategyForm
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'placeholder': 'e.g., Conservative BTC Bot'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'rows': 4,
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
            }),
            'invested_coin': forms.Select(attrs={
                'class': 'form-select bg-transparent border-secondary text-light',
            }),
            'strategy_type': forms.TextInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
            }),
            'min_investment': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'step': '0.01',
                'min': '1',
            }),
            'management_fee': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
            'risk_level': forms.Select(attrs={
                'class': 'form-select bg-transparent border-secondary text-light',
            }),
            'ai_accuracy': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
            'min_holding_period': forms.NumberInput(attrs={
                'class': 'form-control bg-transparent border-secondary text-light',
                'min': '0',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select bg-transparent border-secondary text-light',
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'name': 'Strategy Name',
            'description': 'Full Description',
            'short_description': 'Short Description',
            'invested_coin': 'Invested Coin',
            'strategy_type': 'Strategy Type',
            'min_investment': 'Minimum Investment (USD)',
            'management_fee': 'Management Fee (% per year)',
            'risk_level': 'Risk Level',
            'ai_accuracy': 'AI Accuracy (%)',
            'min_holding_period': 'Minimum Holding Period (months)',
            'status': 'Status',
            'is_featured': 'Featured Strategy',
            'is_public': 'Publicly Visible',
        }


class SpinForm(forms.Form):
    """
    Form for spinning up or down a strategy's price.
    Used by both spin up and spin down views.
    """
    
    amount = forms.DecimalField(
        max_digits=20,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control bg-transparent border-secondary text-light',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '50.00'
        }),
        label='Amount',
        help_text='Amount to change the price by (must be greater than 0)'
    )
    
    reason = forms.CharField(
        required=False,  # Will be validated per view (required for spin down)
        widget=forms.Textarea(attrs={
            'class': 'form-control bg-transparent border-secondary text-light',
            'rows': 2,
            'placeholder': 'e.g., Market rally, positive news...'
        }),
        label='Reason',
        help_text='Optional explanation for the price change'
    )
    
    def clean_amount(self):
        """Ensure amount is positive"""
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Amount must be greater than 0.')
        return amount