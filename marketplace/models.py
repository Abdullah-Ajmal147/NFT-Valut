from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
# Create your models here.

class Product(models.Model):
    name = models.CharField(max_length=255)
    featured = models.BooleanField(default=False)
    description = models.TextField()
    price = models.DecimalField(max_digits=18, decimal_places=8)
    image = models.ImageField(upload_to='products/')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):  
        return f"{self.user.username} - {self.product.name}"
    
# class Order(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     products = models.ManyToManyField(Product, through='OrderItem')
#     total_amount = models.DecimalField(max_digits=18, decimal_places=8)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     def __str__(self):
#         return f"{self.user.username} - {self.total_amount}"
class depositAddress(models.Model):
    eth_deposit_address =  models.CharField(max_length=66, blank=True, null=True)
    usdt_deposit_address =  models.CharField(max_length=66, blank=True, null=True)

    def __str__(self):
        return f"ETH: {self.eth_deposit_address}, USDT: {self.usdt_deposit_address}"

    
class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    eth_balance = models.DecimalField(max_digits=18, decimal_places=8, default=0)

    usdt_balance = models.DecimalField(max_digits=18, decimal_places=8, default=0)

    eth_deposit_address = models.CharField(max_length=66, blank=True, null=True)
    usdt_deposit_address = models.CharField(max_length=66, blank=True, null=True)

    def add_commission(self, amount):
        """Add commission to USDT balance."""
        self.usdt_balance += amount
        self.save()

    def __str__(self):
        return f"{self.user.username}'s Wallet"
    
class CommissionClaim(models.Model):
    ownership = models.ForeignKey('NFTOwnership', on_delete=models.CASCADE, related_name='commission_claims')
    day_number = models.PositiveIntegerField()  # Day 1 to 63
    commission_amount = models.DecimalField(max_digits=18, decimal_places=8)
    claim_date = models.DateTimeField(null=True, blank=True)  # When claimed
    is_claimed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Day {self.day_number} commission for {self.ownership}: {self.commission_amount}"

# New model to track ownership quantities
class NFTOwnership(models.Model):
    nft = models.ForeignKey('NFT', on_delete=models.CASCADE, related_name='ownerships')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='nft_holdings')
    quantity = models.PositiveIntegerField(default=1)
    acquired_at = models.DateTimeField(auto_now_add=True)

    frozen_amount = models.DecimalField(max_digits=18, decimal_places=8, default=0)  # Frozen purchase amount
    release_date = models.DateTimeField(null=True, blank=True)  # When frozen amount is released
    total_commission_earned = models.DecimalField(max_digits=18, decimal_places=8, default=0)  # Tracks total commission

    commission_claim_date = models.DateTimeField(null=True, blank=True)  # Date when commission was claimed
    today_commission_claimed = models.DecimalField(max_digits=18, decimal_places=8, default=0)  # Total claimed commission

    remaining_day_number = models.PositiveIntegerField(default=0)  # Remaining days for commission calculation
    day_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('nft', 'owner')

    def __str__(self):
        return f"{self.owner.username} owns qunatity {self.quantity} of {self.nft.name}"

    def calculate_daily_commission(self):
        # Ensure commission_claim_date is either None or in the past
        print("Calculating daily commission...")
        print(f"Current commission claim date: {self.commission_claim_date}")
        print(f"Current day number: {self.day_number}")
        print(f"Current date: {timezone.now()}")
        if self.commission_claim_date > timezone.now():
            daily_increment = Decimal('0.0005')  # Increase by 0.05% each day
            if self.day_number < 20:
                initial_rate = Decimal('0.01')  
            elif self.day_number < 40:  
                initial_rate = Decimal('0.015')
            elif self.day_number < 60:
                initial_rate = Decimal('0.02')
            else:
                initial_rate = Decimal('0.005')

            commission_rate = initial_rate + (daily_increment * (self.day_number - 1))
            
            # Using full decimal precision for the NFT price
            self.day_number += 1
            self.today_commission_claimed = self.nft.price * commission_rate
            self.commission_claim_date = timezone.now()
            self.save()
            return True, self.today_commission_claimed
        else:
            # Today's commission already claimed, please visit tomorrow
            return False, 0

class NFT(models.Model):
    name = models.CharField(max_length=255)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)  # e.g., 5% commission
    description = models.TextField()
    image = models.ImageField(upload_to='nfts/')
    token_id = models.CharField(max_length=255, unique=True)
    contract_address = models.CharField(max_length=42)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_nfts')
    price = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    total_supply = models.PositiveIntegerField(default=1)  # New field for total available quantity
    available_supply = models.PositiveIntegerField(default=1)  # Track remaining supply
    is_for_sale = models.BooleanField(default=False)
    is_staked = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    staking_rewards = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    staking_number_of_days = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    rarity_level = models.CharField(max_length=20, choices=[
        ('COMMON', 'Common'),
        ('RARE', 'Rare'),
        ('EPIC', 'Epic'),
        ('LEGENDARY', 'Legendary')
    ])
    boost_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    last_trade_price = models.DecimalField(max_digits=18, decimal_places=8, null=True)
    price_change_24h = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_trades = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} (#{self.token_id})"

    def calculate_commission(self, price):
        direct_commission = price * Decimal(settings.DIRECT_REFERRAL_RATE)
        second_level_commission = price * Decimal(settings.SECOND_LEVEL_RATE)
        return direct_commission, second_level_commission

    def calculate_rewards(self, user):
        base_reward = self.price * Decimal(str(self.boost_multiplier))
        user_tier = user.get_reward_tier()
        if user_tier:
            tier_multiplier = settings.REWARD_TIERS[user_tier]['staking_multiplier']
            return base_reward * Decimal(str(tier_multiplier))
        return base_reward

    def apply_cashback(self, user):
        user_tier = user.get_reward_tier()
        if user_tier:
            cashback_rate = settings.REWARD_TIERS[user_tier]['cashback']
            return self.price * Decimal(str(cashback_rate))
        return Decimal('0')

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
        ('COMMISSION', 'Commission'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    CURRENCY_CHOICES = [
        ('ETH', 'Ethereum'),
        ('USDT', 'Tether (USDT)'),
    ]

    nft = models.ForeignKey('NFT', on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sales', null=True, blank=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    price = models.DecimalField(max_digits=18, decimal_places=8)
    quantity = models.PositiveIntegerField(default=1)
    commission_amount = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='ETH')  # Ensure this line exists
    transaction_hash = models.CharField(max_length=66, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    withdraw_address =  models.CharField(max_length=66, blank=True, null=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.nft.name if self.nft else 'Wallet'} - {self.price} {self.currency}"

    class Meta:
        ordering = ['-created_at']