from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    wallet_address = forms.CharField(
        max_length=42,
        required=False,
        help_text='Your Ethereum wallet address (optional)'
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'wallet_address')

    def clean_wallet_address(self):
        address = self.cleaned_data.get('wallet_address')
        if address and not address.startswith('0x'):
            raise forms.ValidationError('Invalid Ethereum address format')
        return address

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'wallet_address')

    def clean_wallet_address(self):
        address = self.cleaned_data.get('wallet_address')
        if address and not address.startswith('0x'):
            raise forms.ValidationError('Invalid Ethereum address format')
        return address 