from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('pools/', views.PoolListView.as_view(), name='pool_list'),
    path('pools/<int:pk>/', views.PoolDetailView.as_view(), name='pool_detail'),
    path('pools/<int:pk>/invest/', views.InvestmentCreateView.as_view(), name='invest'),
    path('my-investments/', views.MyInvestmentsView.as_view(), name='my_investments'),
    path('referrals/', views.ReferralDashboardView.as_view(), name='referral_dashboard'),
]