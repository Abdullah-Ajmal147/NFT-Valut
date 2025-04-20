from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.core.validators import RegexValidator

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Enter a valid email address")
    wallet_address = forms.CharField(
        max_length=42,
        required=False,
        help_text="Your USDT(TRC-20) or Ethereum wallet address (optional)",
        # validators=[
        #     RegexValidator(
        #         regex=r'^0x[a-fA-F0-9]{40}$|^T[a-zA-Z0-9]{33}$',
        #         message="Invalid wallet address format. Must be a valid Ethereum (0x...) or TRON (T...) address."
        #     )
        # ]
    )
    referrer_code = forms.CharField(
        max_length=10,
        required=False,
        help_text="Enter a referral code (optional)",
        widget=forms.TextInput(attrs={'placeholder': 'Referral Code'})
    )

    class Meta:
        model = CustomUser
        # Update fields to use the new name
        fields = ('username', 'email', 'password1', 'password2', 'wallet_address', 'referrer_code')

    # Rename this method to match the new field name
    def clean_referrer_code(self):
        code = self.cleaned_data.get('referrer_code')
        if code:
            try:
                referrer = CustomUser.objects.get(referral_code=code)
                # if not referrer.is_email_verified:
                #     raise forms.ValidationError("Referrer must have a verified email.")
            except CustomUser.DoesNotExist:
                raise forms.ValidationError("Invalid referral code. No user found with this code.")
        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        # Let the model handle generating its own referral_code
        if commit:
            user.save()
            # Use the renamed field
            referrer_code = self.cleaned_data.get('referrer_code')
            if referrer_code:
                try:
                    referrer = CustomUser.objects.get(referral_code=referrer_code)
                    if referrer != user: #and referrer.is_email_verified:
                        user.referrer = referrer
                        user.save()
                except CustomUser.DoesNotExist:
                    pass
        return user
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'wallet_address')

    def clean_wallet_address(self):
        address = self.cleaned_data.get('wallet_address')
        if address and not address.startswith('0x'):
            raise forms.ValidationError('Invalid Ethereum address format')
        return address 