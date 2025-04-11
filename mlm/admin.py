from django.contrib import admin
from .models import StakingPool, Staking, Commission

@admin.register(StakingPool)
class StakingPoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    
    # fieldsets = (
    #     ('Basic Information', {
    #         'fields': ('name', 'description')
    #     }),
    #     ('Status', {
    #         'fields': ('is_active',)
    #     }),
    # )

@admin.register(Staking)
class StakingAdmin(admin.ModelAdmin):
    list_display = ('user', 'nft', 'pool', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
    search_fields = ('user__username', 'nft__name', 'pool__name')
    ordering = ('-start_date',)
    
    # fieldsets = (
    #     ('Stake Information', {
    #         'fields': ('user', 'nft', 'pool')
    #     }),
    #     ('Period', {
    #         'fields': ('start_date', 'end_date')
    #     }),
    # )

@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'commission_type', 'created_at')
    list_filter = ('commission_type', 'created_at')
    search_fields = ('user__username', 'transaction_hash')
    ordering = ('-created_at',)
    
    # fieldsets = (
    #     ('Commission Details', {
    #         'fields': ('user', 'amount', 'commission_type')
    #     }),
    #     ('Blockchain Information', {
    #         'fields': ('transaction_hash',)
    #     }),
    #     ('Description', {
    #         'fields': ('description',)
    #     }),
    # )
