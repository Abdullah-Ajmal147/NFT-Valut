from django import forms
from .models import NFT

class NFTForm(forms.ModelForm):
    class Meta:
        model = NFT
        fields = ['name', 'description', 'image', 'price', 'token_id', 'contract_address']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'step': '0.00000001'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError('Price must be greater than 0')
        return price

    def clean_token_id(self):
        token_id = self.cleaned_data.get('token_id')
        if NFT.objects.filter(token_id=token_id).exists():
            raise forms.ValidationError('This token ID already exists')
        return token_id

    def clean_contract_address(self):
        address = self.cleaned_data.get('contract_address')
        if not address.startswith('0x') or len(address) != 42:
            raise forms.ValidationError('Invalid Ethereum address format')
        return address 