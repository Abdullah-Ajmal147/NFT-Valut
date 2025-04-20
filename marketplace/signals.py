from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal
from .models import Wallet, Transaction  # Adjust the import based on your project structure

@receiver(pre_save, sender=Transaction)
def handle_transaction_status_change(sender, instance, **kwargs):
    """
    Signal to distribute referral commissions when a Transaction's status changes to 'COMPLETED'
    and transaction_type is 'DEPOSIT'.
    """
    # Check if this is an update (not a new instance)
    if instance.pk:
        try:
            # Fetch the previous instance from the database
            previous = Transaction.objects.get(pk=instance.pk)
            
            # Check if status is changing to 'COMPLETED' and transaction_type is 'DEPOSIT'
            if (
                previous.status != 'COMPLETED'
                and instance.status == 'COMPLETED'
                and instance.transaction_type == 'DEPOSIT'
            ):
                try:
                    # Get the user's wallet
                    wallet = instance.buyer.wallet
                    
                    # Add the deposit amount to the user's wallet based on currency
                    deposit_amount = instance.price
                    
                    if instance.currency == 'USDT':
                        wallet.usdt_balance += deposit_amount
                    elif instance.currency == 'ETH':
                        wallet.eth_balance += deposit_amount
                    wallet.save()
                    
                    # Distribute referral commissions (only for USDT)
                    if instance.currency == 'USDT':
                        wallet._distribute_referral_commissions(deposit_amount)
                        
                except Wallet.DoesNotExist:
                    # Create wallet if it doesn't exist
                    from marketplace.models import Wallet
                    wallet = Wallet.objects.create(user=instance.buyer)
                    
                    # Add deposit and process referral if it's USDT
                    if instance.currency == 'USDT':
                        wallet.usdt_balance = instance.price
                        wallet.save()
                        wallet._distribute_referral_commissions(instance.price)
                    elif instance.currency == 'ETH':
                        wallet.eth_balance = instance.price
                        wallet.save()
                        
        except Transaction.DoesNotExist:
            return 