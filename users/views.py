from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.views.generic import ListView
from .models import CustomUser, ReferralReward
from .forms import UserRegistrationForm, UserProfileForm
from marketplace.models import NFT, NFTOwnership, Transaction, Wallet, depositAddress
from mlm.models import Commission
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
import random
import string
from django.urls import reverse
from decimal import Decimal
from django.db import transaction

# def register(request):
#     """Register a new user"""
#     if request.method == 'POST':
#         form = UserRegistrationForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.is_active = True  # User can login but features are restricted
#             user.is_email_verified = False
#             user.email_verification_token = user.generate_verification_token()
#             user.email_token_created_at = timezone.now()
#             user.save()
            
#             # Send verification email
#             verification_url = request.build_absolute_uri(
#                 reverse('users:verify_email', args=[user.email_verification_token])
#             )
#             send_mail(
#                 'Verify your NFTVault account',
#                 f'Click the following link to verify your email: {verification_url}',
#                 settings.DEFAULT_FROM_EMAIL,
#                 [user.email],
#                 fail_silently=False,
#             )
            
#             messages.success(request, 'Registration successful! Please check your email to verify your account.')
#             return redirect('users:login')
#     else:
#         form = UserRegistrationForm()
#     return render(request, 'users/register.html', {'form': form})


@login_required
def confirm_deposit(request):
    if request.method == 'POST':
        try:
            # Get form data
            amount = Decimal(request.POST.get('amount', 0))
            transaction_hash = request.POST.get('transaction_hash', '')
            
            print("Files in request:", request.FILES)
            print("POST data:", request.POST)
            
            # Process file upload if provided
            screenshot = None
            if 'screenshot' in request.FILES:
                screenshot = request.FILES['screenshot']
                
            # Validate the amount
            if amount <= 0:
                messages.error(request, "Deposit amount must be greater than zero.")
                return redirect('users:wallet')
            
            print("screenshot", screenshot)
            
            # Create a pending deposit transaction
            from marketplace.models import Transaction, Wallet
            transaction = Transaction.objects.create(
                buyer=request.user,
                price=amount,
                currency='USDT',
                transaction_type='DEPOSIT',
                status='PENDING',
                transaction_hash=transaction_hash,
                screenshot=screenshot  # Assuming you have this field in your Transaction model
            )
            # wallet = Wallet.objects.get_or_create(
            #     user=request.user
            # )
            
            # Send notification to admins about new deposit
            # This could be done via email, admin notification, etc.
            
            messages.success(request, "Your deposit has been recorded and is pending confirmation. This usually takes 2-3 hours.")
            return redirect('users:wallet')
            
        except (ValueError, TypeError) as e:
            messages.error(request, f"Invalid deposit amount provided.{str(e)}")
            return redirect('users:wallet')
    
    # If not POST, redirect to wallet page
    return redirect('users:wallet')

import logging

logger = logging.getLogger(__name__)
def register(request):
    """Register a new user with optional referral code."""
    initial_data = {}
    logger.debug(f"Request GET: {request.GET}")
    referral_code = request.GET.get('ref')
    logger.debug(f"Referral code from GET: {referral_code}")
    if referral_code:
        initial_data['referral_code'] = referral_code

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.is_active = True
                user.is_email_verified = False
                user.email_verification_token = user.generate_verification_token()
                user.email_token_created_at = timezone.now()

                # Handle referral
                referral_code = form.cleaned_data.get('referral_code')
                logger.debug(f"Referral code from form: {referral_code}")
                if referral_code:
                    try:
                        referrer = CustomUser.objects.get(referral_code=referral_code)
                        if referrer != user and referrer.is_email_verified:
                            user.referrer = referrer
                            logger.info(f"Assigned referrer {referrer.username} to user {user.username}")
                        else:
                            messages.warning(request, "Referral code ignored: Invalid or unverified referrer.")
                    except CustomUser.DoesNotExist:
                        messages.warning(request, "Invalid referral code provided.")
                
                user.save()
                logger.info(f"User {user.username} registered successfully")

                verification_url = request.build_absolute_uri(
                    reverse('users:verify_email', args=[user.email_verification_token])
                )
                # Uncomment when email is configured
                # send_mail(
                #     'Verify your NFTVault account',
                #     f'Click the following link to verify your email: {verification_url}',
                #     settings.EMAIL_HOST_USER,
                #     [user.email],
                #     fail_silently=False,
                # )

                messages.success(request, 'Registration successful! Please check your email to verify your account.')
                return redirect('users:login')
        else:
            logger.warning(f"Form validation failed: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm(initial=initial_data)

    return render(request, 'users/register.html', {'form': form})

def verify_email(request, token):
    """Verify user email and assign referral rewards."""
    try:
        user = CustomUser.objects.get(email_verification_token=token)
        # Check if token is valid (e.g., not expired)
        if user.email_token_created_at and (
            timezone.now() - user.email_token_created_at
        ).total_seconds() <= 86400:  # 24-hour expiry
            with transaction.atomic():
                if not user.is_email_verified:
                    user.is_email_verified = True
                    user.email_verification_token = ''  # Clear token
                    user.save()

                    # Award referral bonuses
                    if user.referrer:
                        referrer = user.referrer
                        # Direct referral bonus (e.g., 10 units)
                        ReferralReward.objects.create(
                            referrer=referrer,
                            referred_user=user,
                            level=1,
                            amount=Decimal('10.00'),
                            description="Direct referral signup bonus"
                        )
                        referrer.total_earnings += Decimal('10.00')
                        referrer.available_balance += Decimal('10.00')
                        referrer.save()

                        # Second-level referral bonus (e.g., 5 units)
                        if referrer.referrer:
                            second_referrer = referrer.referrer
                            ReferralReward.objects.create(
                                referrer=second_referrer,
                                referred_user=user,
                                level=2,
                                amount=Decimal('5.00'),
                                description="Second-level referral signup bonus"
                            )
                            second_referrer.total_earnings += Decimal('5.00')
                            second_referrer.available_balance += Decimal('5.00')
                            second_referrer.save()

                    messages.success(request, 'Email verified successfully! You can now access all features.')
                    return redirect('users:login')
                else:
                    messages.info(request, 'Email already verified.')
                    return redirect('users:login')
        else:
            messages.error(request, 'Verification link has expired or is invalid.')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
    
    return render(request, 'users/verify_email.html')

def register_with_referral(request, referral_code):
    """Register a new user with a referral code"""
    try:
        referrer = CustomUser.objects.get(referral_code=referral_code)
        if request.method == 'POST':
            form = UserRegistrationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.referred_by = referrer
                user.save()
                login(request, user)
                messages.success(request, 'Registration successful!')
                return redirect('marketplace:home')
        else:
            form = UserRegistrationForm()
        return render(request, 'users/register.html', {
            'form': form,
            'referrer': referrer
        })
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid referral code')
        return redirect('users:register')

@login_required
def profile(request):
    """View user profile"""
    return render(request, 'users/profile.html', {
        'user': request.user
    })

@login_required
def profile_edit(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'users/profile_edit.html', {'form': form})

# @login_required
# def wallet(request):
#     """View user's wallet and transaction history"""
#     transactions = Transaction.objects.filter(
#         buyer=request.user
#     ).order_by('-created_at')[:10]
    
#     commissions = Commission.objects.filter(
#         user=request.user,
#         is_paid=False
#     ).order_by('-created_at')
    
#     return render(request, 'users/wallet.html', {
#         'transactions': transactions,
#         'commissions': commissions
#     })
from marketplace.models import Transaction
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
import random

@login_required
def wallet(request):
    # Ensure wallet exists
    address = depositAddress.objects.filter(usdt_deposit_address__isnull=False).first()
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    if created:
        wallet.eth_deposit_address = address.eth_deposit_address # f"TRX_{random.randint(1000, 9999)}_SAMPLE"  # Mock address
        wallet.usdt_deposit_address = address.usdt_deposit_address  #f"USDT_{random.randint(1000, 9999)}_SAMPLE"  # Mock address
        wallet.save()

    # Fetch transactions
    transactions = Transaction.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).select_related('nft', 'buyer', 'seller').order_by('-created_at')

    # nft_ownership = NFTOwnership.objects.filter(user=request.user)
    
    # Calculate totals
    total_earnings = sum(t.price for t in transactions.filter(seller=request.user, status='COMPLETED', currency='ETH'))
    total_commissions = sum(t.commission_amount for t in transactions.filter(buyer=request.user, status='COMPLETED', currency='ETH'))
    unpaid_commissions = sum(t.commission_amount for t in transactions.filter(buyer=request.user, status='PENDING', currency='ETH'))
    unpaid_commissions = 90
    
    # Mock USD values (replace with API call)
    eth_usd_value = float(wallet.eth_balance) * 3000  # Example: 1 ETH = $3000
    commissions_usd_value = float(total_commissions) * 3000

    return render(request, 'users/wallet.html', {
        'transactions': transactions,
        'eth_balance': wallet.eth_balance,
        'usdt_balance': wallet.usdt_balance,
        'total_earnings': total_earnings,
        'total_commissions': total_commissions,
        'unpaid_commissions': unpaid_commissions,
        'eth_usd_value': eth_usd_value,
        'commissions_usd_value': commissions_usd_value,
        'eth_deposit_address': wallet.eth_deposit_address,
        'usdt_deposit_address': wallet.usdt_deposit_address,
    })

@login_required
def withdraw(request):
    wallet = Wallet.objects.get(user=request.user)
    if request.method == 'POST':
        amount = request.POST.get('amount')
        address = request.POST.get('address')
        currency = request.POST.get('currency')

        try:
            amount = float(amount)
            print(f"Currency: {currency}, Amount: {amount}, Wallet ETH: {wallet.eth_balance}, USDT: {wallet.usdt_balance}")
            if amount <= 0:
                raise ValidationError("Amount must be positive.")
            if currency == 'ETH' and amount > wallet.eth_balance:
                messages.error(request, "Insufficient ETH balance.")
            elif currency == 'USDT' and amount > wallet.usdt_balance:
                messages.error(request, "Insufficient USDT balance.")
            else:
                Transaction.objects.create(
                    buyer=request.user,
                    seller=None,
                    transaction_type='WITHDRAW',
                    price=amount,
                    currency=currency,
                    withdraw_address=address,
                    status='PENDING'
                )
                if currency == 'ETH':
                    wallet.eth_balance -= int(amount)
                else:
                    wallet.usdt_balance -= int(amount)
                wallet.save()
                messages.success(request, f"Withdrawal of {amount} {currency} requested.")
                return redirect('users:wallet')
        except ValueError:
            messages.error(request, "Invalid amount entered.")
        except ValidationError as e:
            messages.error(request, str(e))
    return redirect('users:wallet')

@login_required
def claim_commissions(request):
    wallet = Wallet.objects.get(user=request.user)

    nft_ownership = NFTOwnership.objects.filter(owner=request.user)
    for ownership in nft_ownership:
        status, amount = ownership.calculate_daily_commission()
        if status:
            wallet.usdt_balance += amount
            wallet.save()

            Transaction.objects.create(
                buyer=request.user,
                transaction_type='COMMISSION',
                price=amount,
                currency='USDT',
                status='COMPLETED'
            )
        
    messages.success(request, f"Today commissions claimed successfully.")
    return redirect('users:wallet')

# Example NFT purchase to demonstrate commission
@login_required
def buy_nft(request, nft_id):
    nft = NFT.objects.get(id=nft_id)
    wallet = Wallet.objects.get(user=request.user)
    if wallet.eth_balance >= nft.price:
        commission = nft.price * (nft.commission_rate / 100)
        Transaction.objects.create(
            nft=nft,
            buyer=request.user,
            seller=nft.creator,
            transaction_type='BUY',
            price=nft.price,
            currency='USDT',
            status='COMPLETED'
        )
        wallet.eth_balance -= nft.price
        Wallet.objects.get(user=nft.creator).eth_balance += (nft.price - commission)
        wallet.save()
        messages.success(request, f"Purchased {nft.name} for {nft.price} ETH.")
    else:
        messages.error(request, "Insufficient ETH balance.")
    return redirect('marketplace:nft_detail', nft_id=nft_id)


# @login_required
# def referrals(request):
#     """View user's referral program status"""
#     direct_referrals = request.user.get_direct_referrals()
#     second_level_referrals = request.user.get_second_level_referrals()
    
#     return render(request, 'users/referrals.html', {
#         'direct_referrals': direct_referrals,
#         'second_level_referrals': second_level_referrals
#     })

@login_required
def referrals(request):
    """View user's referral program status"""
    user = request.user
    direct_referrals = user.get_direct_referrals()
    second_level_referrals = user.get_second_level_referrals()

    # Calculate counts
    level_1_count = direct_referrals.count()
    level_2_count = len(second_level_referrals)  # Since get_second_level_referrals returns a list

    # Calculate total referrals
    total_referrals = level_1_count + level_2_count

    # Calculate total earnings (from wallet's usdt_balance or a specific field)
    total_earnings = user.wallet.usdt_balance if hasattr(user, 'wallet') else Decimal('0.0')

    # Prepare referrals list for the table
    referrals = []
    for referral in direct_referrals:
        referrals.append({
            'username': referral.username,
            'level': 'Level 1',
            'date_joined': referral.created_at,
            'is_active': referral.is_active,
            'earnings': referral.wallet.usdt_balance if hasattr(referral, 'wallet') else Decimal('0.0')
        })
    for referral in second_level_referrals:
        referrals.append({
            'username': referral.username,
            'level': 'Level 2',
            'date_joined': referral.created_at,
            'is_active': referral.is_active,
            'earnings': referral.wallet.usdt_balance if hasattr(referral, 'wallet') else Decimal('0.0')
        })

    return render(request, 'users/referrals.html', {
        'direct_referrals': direct_referrals,
        'second_level_referrals': second_level_referrals,
        'total_referrals': total_referrals,
        'total_earnings': total_earnings,
        'level_1_count': level_1_count,
        'level_2_count': level_2_count,
        'referrals': referrals,
    })

@login_required
def commissions(request):
    """View user's commission history"""
    commissions = Commission.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    return render(request, 'users/commissions.html', {
        'commissions': commissions
    })

# def verify_email(request, token):
#     try:
#         user = CustomUser.objects.get(email_verification_token=token)
#         timeout = timezone.now() - timezone.timedelta(days=1)
        
#         if user.email_token_created_at < timeout:
#             messages.error(request, 'Verification link has expired. Please request a new one.')
#             return redirect('users:resend_verification')
            
#         user.is_email_verified = True
#         user.email_verification_token = ''
#         user.save()
#         messages.success(request, 'Email verified successfully! You can now use all features.')
#         return redirect('users:login')
        
#     except CustomUser.DoesNotExist:
#         messages.error(request, 'Invalid verification link.')
#         return redirect('users:login')

def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email, is_email_verified=False)
            user.email_verification_token = user.generate_verification_token()
            user.email_token_created_at = timezone.now()
            user.save()
            
            verification_url = request.build_absolute_uri(
                reverse('users:verify_email', args=[user.email_verification_token])
            )
            send_mail(
                'Verify your NFTVault account',
                f'Click the following link to verify your email: {verification_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Verification email sent! Please check your inbox.')
            return redirect('users:login')
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'No unverified account found with this email.')
    
    return render(request, 'users/resend_verification.html')
