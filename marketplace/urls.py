from django.urls import path
from . import views

app_name = 'marketplace'  

urlpatterns = [
    path('', views.home, name='home'),
    path('marketplace/', views.marketplace, name='marketplace'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('my-nfts/', views.my_nfts, name='my_nfts'),
    path('featured/', views.my_nfts, name='my_nfts'),

    path('sell_nfts/', views.sell_nfts, name='sell_nfts'),
    path('my-nfts/sell/<int:ownership_id>/', views.sell_nft, name='sell_nft'),

    path('buy_nft/<int:pk>/', views.nft_buy, name='buy_nft'),
    path('nft-create/', views.nft_create, name='nft_create'),
    path('nft-edit/<int:pk>/', views.nft_edit, name='nft_edit'),
    path('nft-detail/<int:pk>/', views.nft_detail, name='nft_detail'),

    # path('nft-list/', views.nft_list, name='nft_list'),
    # path('nft-list/featured/', views.featured_nfts, name='featured_nfts'),
    
] 