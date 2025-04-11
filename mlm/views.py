from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import StakingPool, Staking, Commission
from marketplace.models import NFT

@login_required
def staking_pools(request):
    """View all available staking pools"""
    pools = StakingPool.objects.filter(is_active=True)
    return render(request, 'mlm/staking_pools.html', {
        'pools': pools
    })

@login_required
def staking_pool_detail(request, pk):
    """View details of a specific staking pool"""
    pool = get_object_or_404(StakingPool, pk=pk, is_active=True)
    user_stakes = Staking.objects.filter(
        user=request.user,
        pool=pool,
        is_active=True
    )
    return render(request, 'mlm/staking_pool_detail.html', {
        'pool': pool,
        'user_stakes': user_stakes
    })

@login_required
def my_stakes(request):
    """View user's active stakes"""
    stakes = Staking.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-start_date')
    return render(request, 'mlm/my_stakes.html', {
        'stakes': stakes
    })

@login_required
def claim_staking_rewards(request, pk):
    """Claim rewards from a staked NFT"""
    stake = get_object_or_404(Staking, pk=pk, user=request.user)
    if request.method == 'POST':
        rewards = stake.claim_rewards()
        if rewards > 0:
            # Create commission record for staking rewards
            Commission.objects.create(
                user=request.user,
                transaction=stake.nft.transactions.first(),
                commission_type='STAKING',
                amount=rewards
            )
            messages.success(request, f'Successfully claimed {rewards} rewards!')
        else:
            messages.warning(request, 'No rewards available to claim yet.')
        return redirect('mlm:my_stakes')
    return render(request, 'mlm/claim_rewards.html', {
        'stake': stake
    })

@login_required
def commission_history(request):
    """View user's commission history"""
    commissions = Commission.objects.filter(
        user=request.user
    ).order_by('-created_at')
    return render(request, 'mlm/commission_history.html', {
        'commissions': commissions
    })

@login_required
def stake_nft(request, pool_id):
    pool = get_object_or_404(StakingPool, id=pool_id, is_active=True)
    
    if request.method == 'POST':
        nft_id = request.POST.get('nft_id')
        stake_period = int(request.POST.get('stake_period', 0))
        
        try:
            nft = NFT.objects.get(id=nft_id, owner=request.user)
            
            # Validate stake period
            if stake_period < pool.minimum_stake_period:
                messages.error(request, f'Minimum stake period is {pool.minimum_stake_period} days')
                return redirect('mlm:staking_pool_detail', pk=pool_id)
            
            # Create stake
            end_date = timezone.now() + timezone.timedelta(days=stake_period)
            stake = Staking.objects.create(
                user=request.user,
                nft=nft,
                pool=pool,
                start_date=timezone.now(),
                end_date=end_date
            )
            
            messages.success(request, f'Successfully staked {nft.name} for {stake_period} days')
            return redirect('mlm:staking_pool_detail', pk=pool_id)
            
        except NFT.DoesNotExist:
            messages.error(request, 'Invalid NFT selection')
        except Exception as e:
            messages.error(request, f'Error staking NFT: {str(e)}')
    
    return redirect('mlm:staking_pool_detail', pk=pool_id)

# API Views
class CommissionListView(ListView):
    model = Commission
    template_name = 'mlm/commission_list.html'
    context_object_name = 'commissions'
    paginate_by = 10

    def get_queryset(self):
        return Commission.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

class CommissionDetailView(DetailView):
    model = Commission
    template_name = 'mlm/commission_detail.html'
    context_object_name = 'commission'

    def get_queryset(self):
        return Commission.objects.filter(user=self.request.user)
