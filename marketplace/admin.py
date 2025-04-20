from django.contrib import admin
from .models import NFT, CommissionClaim, NFTOwnership, Transaction, Wallet, depositAddress

@admin.register(NFT)
class NFTAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'price', 'token_id', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'token_id', 'contract_address')
    ordering = ('-created_at',)
    
    # fieldsets = (
    #     ('Basic Information', {
    #         'fields': ('name', 'description', 'image')
    #     }),
    #     ('Ownership', {
    #         'fields': ('creator', 'owner')
    #     }),
    #     ('Blockchain Details', {
    #         'fields': ('price', 'token_id', 'contract_address')
    #     }),
    # )

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('nft', 'seller', 'buyer', 'price', 'transaction_hash', 'created_at', 'status', 'transaction_type')
    list_filter = ('created_at', 'status', 'transaction_type')
    search_fields = ('nft__name', 'transaction_hash', 'seller__username', 'buyer__username')
    ordering = ('-created_at',)
    
    # fieldsets = (
    #     ('Transaction Details', {
    #         'fields': ('nft', 'seller', 'buyer', 'price')
    #     }),
    #     ('Blockchain Information', {
    #         'fields': ('transaction_hash',)
    #     }),
    # )

admin.site.register(Wallet)
admin.site.register(depositAddress)
admin.site.register(CommissionClaim)
admin.site.register(NFTOwnership)
