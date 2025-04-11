from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class Investment(models.Model):
    INVESTMENT_STATUS = (
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('WITHDRAWN', 'Withdrawn')
    )
    
    investor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_invested = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=INVESTMENT_STATUS, default='ACTIVE')
    referrer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='investment_referrals')
    
    def calculate_earnings(self):
        return sum(earning.amount for earning in self.earnings.all())

class InvestmentPool(models.Model):
    POOL_TYPES = (
        ('NFT', 'NFT Investment'),
        ('CRYPTO', 'Cryptocurrency'),
        ('ECOMMERCE', 'E-Commerce')
    )
    
    name = models.CharField(max_length=100)
    pool_type = models.CharField(max_length=20, choices=POOL_TYPES)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class Earning(models.Model):
    EARNING_TYPES = (
        ('PROFIT', 'Investment Profit'),
        ('REFERRAL', 'Referral Bonus')
    )
    
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='earnings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    earning_type = models.CharField(max_length=20, choices=EARNING_TYPES)
    date_earned = models.DateTimeField(auto_now_add=True)
    
    @classmethod
    def calculate_referral_bonus(cls, investment_amount):
        return Decimal(investment_amount) * Decimal('0.10')  # 10% referral bonus 