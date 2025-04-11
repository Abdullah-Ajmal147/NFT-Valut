from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from .models import NFT, CommissionClaim, NFTOwnership, Transaction, Product, Cart, Wallet
from .forms import NFTForm
from decimal import Decimal

def home(request):
    featured_products = NFT.objects.filter(is_staked=True)[:6]
    context = {
        'nfts': featured_products,
    }
    return render(request, 'marketplace/home.html', context)

def marketplace(request):
    nfts = NFT.objects.filter(is_for_sale=True).order_by('-created_at')
    nft_is_featured = NFT.objects.filter(is_featured=True).order_by('-created_at')
    feature_nfts = nft_is_featured[:4]  # Example: First 4 as featured

    # Pagination
    per_page = int(request.GET.get('per_page', 12))
    paginator = Paginator(nfts, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'marketplace/marketplace.html', {
        'nfts': page_obj,
        'feature_nfts': feature_nfts,
        'paginator': paginator,
        'page_obj': page_obj,
    })

def feature_nfts(request):
    """Marketplace view showing all NFTs for sale"""
    latest_nfts = NFT.objects.all().order_by('-created_at') 
    feature_nfts = NFT.objects.filter(is_for_sale=True)
    
    context = {
        'nfts': latest_nfts,
        'feature_nfts': feature_nfts,
    }
    return render(request, 'marketplace/marketplace.html', context)

@login_required
def nft_delete(request, pk):
    """Delete an NFT"""
    nft = get_object_or_404(NFT, pk=pk, owner=request.user)
    if request.method == 'POST':
        nft.delete()
        messages.success(request, 'NFT deleted successfully!')
        return redirect('marketplace:my_nfts')
    return render(request, 'marketplace/nft_confirm_delete.html', {
        'nft': nft
    })

from django.core.paginator import Paginator
@login_required
def my_nfts(request):
    # Query NFTOwnership instead of NFT to get user's owned NFTs
    ownerships = NFTOwnership.objects.filter(owner=request.user).select_related('nft').order_by('-acquired_at')
    
    # Pagination
    paginator = Paginator(ownerships, 4)  # Show 9 NFTs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'marketplace/my_nfts.html', {
        'ownerships': page_obj,
        'page_obj': page_obj,
    })
@login_required
def nft_buy(request, pk):
    nft = get_object_or_404(NFT, pk=pk)
    wallet = Wallet.objects.filter(user=request.user).first()
    available_balance = wallet.usdt_balance if wallet else 0

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        total_cost = nft.price * quantity

        if quantity > nft.available_supply:
            messages.error(request, 'Not enough supply available!')
            return render(request, 'marketplace/nft_buy.html', {
                'nft': nft, 'available_balance': available_balance
            })

        if total_cost > available_balance:
            messages.error(request, 'Insufficient balance!')
            return render(request, 'marketplace/nft_buy.html', {
                'nft': nft, 'available_balance': available_balance
            })

        # Create or update ownership
        ownership, created = NFTOwnership.objects.get_or_create(
            nft=nft, owner=request.user, defaults={'quantity': quantity}
        )
        if not created:
            ownership.quantity += quantity
            ownership.frozen_amount += total_cost
        else:
            ownership.frozen_amount = total_cost

        ownership.release_date = timezone.now() + timedelta(days=int(nft.staking_number_of_days))
        ownership.save()

        # Update wallet
        wallet.usdt_balance -= total_cost
        wallet.save()

        # Update NFT
        nft.available_supply -= quantity
        nft.total_trades += 1
        nft.last_trade_price = nft.price
        if nft.available_supply == 0:
            nft.is_for_sale = False
        nft.save()

        # Log transaction
        Transaction.objects.create(
            nft=nft,
            buyer=request.user,
            seller=nft.creator if nft.available_supply > 0 else None,
            transaction_type='BUY',
            price=total_cost,
            quantity=quantity,
            status='COMPLETED',
        )

        messages.success(request, f'Successfully purchased {quantity} unit(s) of {nft.name}!')
        return redirect('marketplace:nft_detail', pk=nft.pk)

    return render(request, 'marketplace/nft_buy.html', {
        'nft': nft, 'available_balance': available_balance
    })


@login_required
def claim_commission(request, ownership_id):
    ownership = get_object_or_404(NFTOwnership, id=ownership_id, owner=request.user)
    today = timezone.now().date()
    days_passed = (today - ownership.acquired_at.date()).days + 1

    if days_passed > ownership.nft.staking_number_of_days or days_passed < 1:
        messages.error(request, "No commissions available for today.")
        return redirect('marketplace:my_nfts')

    if not ownership.is_commission_claimable_today():
        messages.info(request, "Today's commission has already been claimed.")
        return redirect('marketplace:my_nfts')

    commission_claim = CommissionClaim.objects.filter(
        ownership=ownership, day_number=days_passed, is_claimed=False
    ).first()

    if not commission_claim:
        messages.error(request, "No commission available for today.")
        return redirect('marketplace:my_nfts')

    if request.method == 'POST':
        wallet = request.user.wallet
        wallet.add_commission(commission_claim.commission_amount)
        commission_claim.is_claimed = True
        commission_claim.claim_date = timezone.now()
        commission_claim.save()

        ownership.total_commission_earned += commission_claim.commission_amount
        ownership.remaing_day_number -= 1
        ownership.save()

        Transaction.objects.create(
            buyer=request.user,
            transaction_type='COMMISSION',
            price=commission_claim.commission_amount,
            currency='USDT',
            status='COMPLETED',
        )

        messages.success(request, f"Claimed {commission_claim.commission_amount} USDT for day {days_passed}!")
        return redirect('marketplace:my_nfts')

    return render(request, 'marketplace/claim_commission.html', {
        'ownership': ownership,
        'commission_amount': commission_claim.commission_amount,
        'day_number': days_passed,
    })

from django.utils import timezone
from datetime import timedelta
@login_required
def nft_sell(request, pk):
    """Put an NFT up for sale"""
    nft = get_object_or_404(NFT, pk=pk, owner=request.user)
    if request.method == 'POST':
        price = Decimal(request.POST.get('price'))
        nft.price = price
        nft.is_for_sale = True
        nft.save()
        messages.success(request, 'NFT listed for sale successfully!')
        return redirect('marketplace:nft_detail', pk=nft.pk)
    return render(request, 'marketplace/nft_sell.html', {
        'nft': nft
    })

@login_required
def sell_nft(request, ownership_id):
    """Handle the sale of a single NFT from the user's collection"""
    ownership = get_object_or_404(NFTOwnership, id=ownership_id, owner=request.user)
    nft = ownership.nft
    print(f"Ownerships: {ownership}")
    print(f"NFT: {nft}")
    
    if request.method == 'POST':
        print(f"POST data: {request.POST}")
        quantity = int(request.POST.get('quantity', 1))
        price = Decimal(request.POST.get('price'))
        listing_duration = int(request.POST.get('listing_duration', 7))
        allow_offers = 'allow_offers' in request.POST
        listing_notes = request.POST.get('listing_notes', '')
        
        # Validate quantity
        if quantity <= 0 or quantity > ownership.quantity:
            messages.error(request, f'Invalid quantity. You own {ownership.quantity} units of this NFT.')
            return redirect('marketplace:sell_nft', ownership_id=ownership_id)
        
        # Create expiry date if applicable
        expiry_date = None
        if listing_duration > 0:
            expiry_date = timezone.now() + timedelta(days=listing_duration)
        
        # Update ownership quantity if not selling all
        if quantity < ownership.quantity:
            ownership.quantity -= quantity
            ownership.save()
        else:
            ownership.delete()
        
        messages.success(request, f'Successfully listed {quantity} unit(s) of {nft.name} for {price} ETH each.')
        return redirect('marketplace:my_listings')
    print(f"Ownership: {ownership}")
    print(f"NFT: {nft}")
    
    return render(request, 'marketplace/sell_nft.html', {
        'ownership': ownership,
        'nft': nft
    })

@login_required
def sell_nfts(request):
    """Handle listing multiple NFTs for sale at once"""
    # Get all NFTs owned by the user
    ownerships = NFTOwnership.objects.filter(owner=request.user).select_related('nft').order_by('-acquired_at')
    
    if request.method == 'POST':
        selected_nfts = request.POST.getlist('selected_nfts')
        listing_duration = int(request.POST.get('listing_duration', 7))
        allow_offers = 'allow_offers' in request.POST
        listing_notes = request.POST.get('listing_notes', '')
        
        # Calculate expiry date if applicable
        expiry_date = None
        if listing_duration > 0:
            expiry_date = timezone.now() + timedelta(days=listing_duration)
        
        # Process each selected NFT
        listings_created = 0
        for ownership_id in selected_nfts:
            try:
                ownership = NFTOwnership.objects.get(id=ownership_id, owner=request.user)
                quantity = int(request.POST.get(f'quantity-{ownership_id}', 1))
                price = Decimal(request.POST.get(f'price-{ownership_id}', ownership.nft.price))

                print(f"Processing NFT: {ownership.nft.name}, Quantity: {quantity}, Price: {price}")
                
                # Validate quantity
                if quantity <= 0 or quantity > ownership.quantity:
                    messages.error(request, f'Invalid quantity for {ownership.nft.name}. Skipping this NFT.')
                    continue

                Transaction.objects.create(
                    buyer=request.user,
                    transaction_type='SELL',
                    price=price,
                    currency='USDT',
                    status='PENDING',
                    quantity=quantity,
                )
                
                # Update ownership quantity if not selling all
                if quantity < ownership.quantity:
                    ownership.quantity -= quantity
                    ownership.save()
                else:
                    ownership.delete()
                
                listings_created += 1
                
            except NFTOwnership.DoesNotExist:
                messages.error(request, f'One of the selected NFTs is no longer in your collection.')
                continue
        
        if listings_created > 0:
            messages.success(request, f'Successfully created {listings_created} NFT listing(s).')
            return redirect('marketplace:my_nfts')
        else:
            messages.error(request, 'No valid listings were created.')
    
    return render(request, 'marketplace/sell_nft.html', {
        'ownerships': ownerships
    })

@login_required
def nft_detail(request, pk):
    """Detailed view of a single NFT"""
    nft = get_object_or_404(NFT, pk=pk)
    return render(request, 'marketplace/nft_detail.html', {
        'nft': nft
    })

@login_required
def nft_create(request):
    """Create a new NFT"""
    if request.method == 'POST':
        form = NFTForm(request.POST, request.FILES)
        if form.is_valid():
            nft = form.save(commit=False)
            nft.creator = request.user
            nft.owner = request.user
            nft.save()
            messages.success(request, 'NFT created successfully!')
            return redirect('marketplace:nft_detail', pk=nft.pk)
    else:
        form = NFTForm()
    return render(request, 'marketplace/nft_form.html', {
        'form': form,
        'title': 'Create NFT'
    })

@login_required
def nft_edit(request, pk):
    """Edit an existing NFT"""
    nft = get_object_or_404(NFT, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = NFTForm(request.POST, request.FILES, instance=nft)
        if form.is_valid():
            form.save()
            messages.success(request, 'NFT updated successfully!')
            return redirect('marketplace:nft_detail', pk=nft.pk)
    else:
        form = NFTForm(instance=nft)
    return render(request, 'marketplace/nft_form.html', {
        'form': form,
        'title': 'Edit NFT'
    })

@login_required
def nft_stake(request, pk):
    """Stake an NFT"""
    nft = get_object_or_404(NFT, pk=pk, owner=request.user)
    if request.method == 'POST':
        # Here you would implement the actual staking logic
        nft.is_staked = True
        nft.save()
        messages.success(request, 'NFT staked successfully!')
        return redirect('marketplace:nft_detail', pk=nft.pk)
    return render(request, 'marketplace/nft_stake.html', {
        'nft': nft
    })

@login_required
def nft_unstake(request, pk):
    """Unstake an NFT"""
    nft = get_object_or_404(NFT, pk=pk, owner=request.user)
    if request.method == 'POST':
        # Here you would implement the actual unstaking logic
        nft.is_staked = False
        nft.save()
        messages.success(request, 'NFT unstaked successfully!')
        return redirect('marketplace:nft_detail', pk=nft.pk)
    return render(request, 'marketplace/nft_unstake.html', {
        'nft': nft
    })

# @login_required
# def my_nfts(request):
#     """View user's owned NFTs"""
#     owned_nfts = NFT.objects.filter(owner=request.user)
#     return render(request, 'marketplace/my_nfts.html', {
#         'owned_nfts': owned_nfts
#     })

@login_required
def create_nft(request):
    if request.method == 'POST':
        form = NFTForm(request.POST, request.FILES)
        if form.is_valid():
            nft = form.save(commit=False)
            nft.creator = request.user
            nft.owner = request.user
            nft.save()
            messages.success(request, 'NFT created successfully!')
            return redirect('marketplace:nft_detail', pk=nft.pk)
    else:
        form = NFTForm()
    
    return render(request, 'marketplace/create_nft.html', {'form': form})

# API Views
class NFTListView(ListView):
    model = NFT
    template_name = 'marketplace/nft_list.html'
    context_object_name = 'nfts'
    paginate_by = 12

    def get_queryset(self):
        queryset = NFT.objects.filter(is_for_sale=True)
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        return queryset

class NFTDetailView(DetailView):
    model = NFT
    template_name = 'marketplace/nft_detail.html'
    context_object_name = 'nft'

def product_list(request):
    products = Product.objects.all()
    context = {
        'products': products,
    }
    return render(request, 'marketplace/product_list.html', context)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    context = {
        'product': product,
    }
    return render(request, 'marketplace/product_detail.html', context)

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
    }
    return render(request, 'marketplace/cart.html', context)

@login_required
def checkout(request):
    cart = Cart.objects.get(user=request.user)
    context = {
        'cart': cart,
    }
    return render(request, 'marketplace/checkout.html', context)
