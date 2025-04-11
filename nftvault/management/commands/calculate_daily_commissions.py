from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from nftvault.models import StakedNFT, Commission, Wallet

class Command(BaseCommand):
    help = 'Calculate and distribute daily commissions for staked NFTs'

    def handle(self, *args, **options):
        # Get all active staked NFTs
        active_stakes = StakedNFT.objects.filter(is_active=True)
        
        for stake in active_stakes:
            # Calculate commission based on staking plan and purchase price
            daily_rate = stake.staking_plan.daily_commission_rate / Decimal('100')
            commission_amount = stake.nft_ownership.purchase_price * daily_rate
            
            # Create commission record
            commission = Commission.objects.create(
                user=stake.nft_ownership.owner,
                staked_nft=stake,
                amount=commission_amount,
                date=timezone.now()
            )
            
            # Add to user's wallet
            wallet, created = Wallet.objects.get_or_create(
                user=stake.nft_ownership.owner, 
                defaults={'balance': 0}
            )
            wallet.balance += commission_amount
            wallet.save()
            
            self.stdout.write(f"Added {commission_amount} commission to {stake.nft_ownership.owner.username}'s wallet")
            
        self.stdout.write(self.style.SUCCESS(f"Processed commissions for {active_stakes.count()} staked NFTs")) 