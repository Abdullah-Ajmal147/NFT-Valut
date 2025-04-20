from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import random
import string
from django.core.validators import RegexValidator
from django.utils import timezone

# class CustomUser(AbstractUser):
#     email = models.EmailField(unique=True)
#     wallet_address = models.CharField(max_length=42, blank=True, null=True, unique=True)
#     referral_code = models.CharField(max_length=10, unique=True, blank=True)
#     referrer = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
#     total_earnings = models.DecimalField(max_digits=18, decimal_places=8, default=0)
#     available_balance = models.DecimalField(max_digits=18, decimal_places=8, default=0)
#     is_verified = models.BooleanField(default=False)
#     is_email_verified = models.BooleanField(default=False)
#     email_verification_token = models.CharField(max_length=100, blank=True)
#     email_token_created_at = models.DateTimeField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.username

#     def save(self, *args, **kwargs):
#         if not self.referral_code:
#             import random
#             import string
#             self.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
#         super().save(*args, **kwargs)

#     def get_referral_link(self):
#         return f"https://nftvalut.pro/ref/{self.referral_code}"

#     def get_total_referrals(self):
#         return self.referrals.count()

#     def get_direct_referrals(self):
#         return self.referrals.filter(referrer=self)

#     def get_second_level_referrals(self):
#         direct_referrals = self.get_direct_referrals()
#         second_level = []
#         for referral in direct_referrals:
#             second_level.extend(referral.get_direct_referrals())
#         return second_level

#     def generate_verification_token(self):
#         return ''.join(random.choices(string.ascii_letters + string.digits, k=32))


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    # Wallet address validation for Ethereum-like addresses (0x + 40 hex chars)
    wallet_address = models.CharField(
        max_length=42,
        blank=True,
        null=True,
        unique=True,
        # validators=[RegexValidator(
        #     regex=r'^0x[a-fA-F0-9]{40}$',
        #     message='Invalid wallet address format'
        # )]
    )
    referral_code = models.CharField(max_length=10, unique=True, blank=True, db_index=True)
    # Self-referential FK for the user who referred this user
    referrer = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_referrals'
    )
    total_earnings = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    available_balance = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    is_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
    email_token_created_at = models.DateTimeField(null=True, blank=True)
    screenshot = models.ImageField(upload_to='users/deposit_screenshots/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username or self.email

    def save(self, *args, **kwargs):
        if not self.referral_code:
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                if not CustomUser.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        if self.referrer == self:
            self.referrer = None
        super().save(*args, **kwargs)

    def get_referral_link(self):
        return f"https://nftvalut.pro/ref/{self.referral_code}"

    def get_total_direct_referrals(self):
        return self.direct_referrals.count()

    def generate_verification_token(self):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        self.email_verification_token = token
        self.email_token_created_at = timezone.now()
        return token
    
    def get_direct_referrals(self):
        return self.direct_referrals.all()

    def get_second_level_referrals(self):
        return CustomUser.objects.filter(referrer__in=self.direct_referrals.all())
    
class ReferralReward(models.Model):
    referrer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='referral_rewards'
    )
    referred_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='referred_rewards'
    )
    level = models.PositiveIntegerField(default=1)  # 1 for direct, 2 for second-level, etc.
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    description = models.CharField(max_length=255, blank=True)  # e.g., "Referral bonus"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('referrer', 'referred_user', 'level')
        indexes = [
            models.Index(fields=['referrer', 'level']),
            models.Index(fields=['referred_user']),
        ]

    def __str__(self):
        return f"{self.referrer} earned {self.amount} for {self.referred_user} (Level {self.level})"