from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone

# Create your models here.

class Commission(models.Model):
    COMMISSION_TYPES = [
        ('DIRECT', 'Direct Referral'),
        ('SECOND_LEVEL', 'Second Level'),
        ('STAKING', 'Staking Reward'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commissions')
    transaction = models.ForeignKey('marketplace.Transaction', on_delete=models.CASCADE, related_name='commissions')
    commission_type = models.CharField(max_length=20, choices=COMMISSION_TYPES)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.commission_type} - {self.user.username} - {self.amount}"

    def mark_as_paid(self):
        self.is_paid = True
        self.paid_at = timezone.now()
        self.save()

class StakingPool(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    apy = models.DecimalField(max_digits=5, decimal_places=2)  # Annual Percentage Yield
    min_stake_amount = models.DecimalField(max_digits=18, decimal_places=8)
    max_stake_amount = models.DecimalField(max_digits=18, decimal_places=8)
    lock_period_days = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.apy}% APY)"

class Staking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stakings')
    nft = models.ForeignKey('marketplace.NFT', on_delete=models.CASCADE, related_name='stakings')
    pool = models.ForeignKey(StakingPool, on_delete=models.CASCADE, related_name='stakings')
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    rewards_claimed = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.nft.name} - {self.amount}"

    def calculate_rewards(self):
        if not self.is_active:
            return Decimal('0')
        
        now = timezone.now()
        if now < self.end_date:
            days_staked = (now - self.start_date).days
        else:
            days_staked = (self.end_date - self.start_date).days
        
        daily_rate = self.pool.apy / Decimal('36500')  # Convert APY to daily rate
        rewards = self.amount * daily_rate * Decimal(str(days_staked))
        return rewards - self.rewards_claimed

    def claim_rewards(self):
        rewards = self.calculate_rewards()
        if rewards > 0:
            self.rewards_claimed += rewards
            self.save()
            return rewards
        return Decimal('0')
