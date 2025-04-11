from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import random
import string

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    wallet_address = models.CharField(max_length=42, blank=True, null=True, unique=True)
    referral_code = models.CharField(max_length=10, unique=True, blank=True)
    referrer = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    total_earnings = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    available_balance = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    is_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    email_token_created_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.referral_code:
            import random
            import string
            self.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save(*args, **kwargs)

    def get_referral_link(self):
        return f"https://yourdomain.com/ref/{self.referral_code}"

    def get_total_referrals(self):
        return self.referrals.count()

    def get_direct_referrals(self):
        return self.referrals.filter(referrer=self)

    def get_second_level_referrals(self):
        direct_referrals = self.get_direct_referrals()
        second_level = []
        for referral in direct_referrals:
            second_level.extend(referral.get_direct_referrals())
        return second_level

    def generate_verification_token(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
