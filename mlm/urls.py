from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'mlm'  # Add this namespace

urlpatterns = [
    path('staking_pools/', views.staking_pools, name='staking_pools'),
    path('staking_pool_detail/<int:pk>/', views.staking_pool_detail, name='staking_pool_detail'),
    path('my-stakes/', views.my_stakes, name='my_stakes'),
    path('claim-rewards/<int:pk>/', views.claim_staking_rewards, name='claim_staking_rewards'),
    path('commission-history/', views.commission_history, name='commission_history'),
    path('stake-nft/<int:pool_id>/', views.stake_nft, name='stake_nft')    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 