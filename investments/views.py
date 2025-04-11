from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Investment, InvestmentPool, Earning
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Sum

User = get_user_model()

@login_required
def make_investment(request):
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        referrer_code = request.POST.get('referrer_code')
        
        if amount < 100:  # Minimum investment check
            messages.error(request, 'Minimum investment amount is $100')
            return redirect('investment_form')
            
        investment = Investment.objects.create(
            investor=request.user,
            amount=amount
        )
        
        # Handle referral bonus if applicable
        if referrer_code:
            try:
                referrer = User.objects.get(referral_code=referrer_code)
                investment.referrer = referrer
                investment.save()
                
                # Create referral bonus earning
                referral_bonus = Earning.calculate_referral_bonus(amount)
                Earning.objects.create(
                    investment=investment,
                    amount=referral_bonus,
                    earning_type='REFERRAL'
                )
            except User.DoesNotExist:
                messages.warning(request, 'Invalid referral code')
        
        messages.success(request, 'Investment successful!')
        return redirect('dashboard')
        
    return render(request, 'investments/invest.html')

@login_required
def dashboard(request):
    investments = Investment.objects.filter(investor=request.user)
    total_invested = sum(inv.amount for inv in investments)
    total_earnings = sum(inv.calculate_earnings() for inv in investments)
    
    context = {
        'investments': investments,
        'total_invested': total_invested,
        'total_earnings': total_earnings
    }
    return render(request, 'investments/dashboard.html', context)

class HomeView(TemplateView):
    template_name = 'home/index.html'

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'home/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's investments
        investments = Investment.objects.filter(investor=user)
        total_invested = investments.aggregate(Sum('amount'))['amount__sum'] or 0
        total_earnings = sum(inv.calculate_earnings() for inv in investments)
        
        # Calculate ROI
        roi = ((total_earnings / total_invested) * 100) if total_invested > 0 else 0
        
        # Get investment distribution
        nft_investments = investments.filter(pool__pool_type='NFT').aggregate(Sum('amount'))['amount__sum'] or 0
        crypto_investments = investments.filter(pool__pool_type='CRYPTO').aggregate(Sum('amount'))['amount__sum'] or 0
        ecommerce_investments = investments.filter(pool__pool_type='ECOMMERCE').aggregate(Sum('amount'))['amount__sum'] or 0
        
        context.update({
            'total_invested': total_invested,
            'total_earnings': total_earnings,
            'roi': round(roi, 2),
            'nft_percentage': round((nft_investments / total_invested * 100) if total_invested > 0 else 0, 2),
            'crypto_percentage': round((crypto_investments / total_invested * 100) if total_invested > 0 else 0, 2),
            'ecommerce_percentage': round((ecommerce_investments / total_invested * 100) if total_invested > 0 else 0, 2),
            'investment_pools': InvestmentPool.objects.all()[:3],
            'referral_earnings': Earning.objects.filter(
                investment__investor=user,
                earning_type='REFERRAL'
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_referrals': Investment.objects.filter(referrer=user).count(),
        })
        return context

class PoolListView(ListView):
    model = InvestmentPool
    template_name = 'investments/pool_list.html'
    context_object_name = 'pools'

class PoolDetailView(DetailView):
    model = InvestmentPool
    template_name = 'investments/pool_detail.html'
    context_object_name = 'pool'

class InvestmentCreateView(LoginRequiredMixin, CreateView):
    model = Investment
    template_name = 'investments/invest.html'
    fields = ['amount', 'payment_method']
    success_url = reverse_lazy('investments:dashboard')
    
    def form_valid(self, form):
        form.instance.investor = self.request.user
        form.instance.pool = InvestmentPool.objects.get(pk=self.kwargs['pk'])
        return super().form_valid(form)

class MyInvestmentsView(LoginRequiredMixin, ListView):
    template_name = 'investments/my_investments.html'
    context_object_name = 'investments'
    
    def get_queryset(self):
        return Investment.objects.filter(investor=self.request.user)

class ReferralDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'referrals/referral_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context.update({
            'referral_earnings': Earning.objects.filter(
                investment__investor=user,
                earning_type='REFERRAL'
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
            'referrals': Investment.objects.filter(referrer=user),
        })
        return context