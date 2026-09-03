from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP, TrustedDevice


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model"""
    
    list_display = [
        'email', 'get_full_name', 'email_verified', 'kyc_status',
        'balance', 'is_active', 'date_joined'
    ]
    list_filter = [
        'email_verified', 'kyc_status', 'is_active', 'is_staff',
        'date_joined', 'last_login'
    ]
    search_fields = ['email', 'username', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']
    
    # Extend the default UserAdmin fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Email Verification', {
            'fields': ('email_verified', 'email_verified_at'),
        }),
        ('KYC Verification', {
            'fields': ('kyc_status', 'kyc_submitted_at', 'kyc_verified_at', 'kyc_rejection_reason'),
        }),
        ('Profile', {
            'fields': ('phone', 'profile_image', 'timezone', 'preferred_currency'),
        }),
        ('Financial', {
            'fields': ('balance', 'total_invested', 'total_deposited', 'total_withdrawn'),
        }),
        ('Security', {
            'fields': ('last_login_ip', 'failed_login_attempts', 'account_locked_until'),
        }),
    )
    
    readonly_fields = [
        'date_joined', 'last_login', 'email_verified_at',
        'kyc_submitted_at', 'kyc_verified_at', 'last_login_ip',
        'last_activity_at'
    ]
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'phone', 'first_name', 'last_name'),
        }),
    )
    
    actions = ['verify_emails', 'approve_kyc', 'reject_kyc', 'lock_accounts']
    
    @admin.action(description='Mark selected users as email verified')
    def verify_emails(self, request, queryset):
        count = 0
        for user in queryset:
            if not user.email_verified:
                user.verify_email()
                count += 1
        self.message_user(request, f'{count} user(s) email verified.')
    
    @admin.action(description='Approve KYC for selected users')
    def approve_kyc(self, request, queryset):
        count = 0
        for user in queryset:
            if user.kyc_status != User.KYC_APPROVED:
                user.approve_kyc()
                count += 1
        self.message_user(request, f'{count} user(s) KYC approved.')
    
    @admin.action(description='Reject KYC for selected users')
    def reject_kyc(self, request, queryset):
        count = 0
        for user in queryset:
            if user.kyc_status != User.KYC_REJECTED:
                user.reject_kyc('Rejected by admin')
                count += 1
        self.message_user(request, f'{count} user(s) KYC rejected.')
    
    @admin.action(description='Lock selected accounts')
    def lock_accounts(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        count = 0
        for user in queryset:
            user.is_active = False
            user.account_locked_until = timezone.now() + timedelta(days=30)
            user.save()
            count += 1
        self.message_user(request, f'{count} account(s) locked.')


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """Admin configuration for OTP model"""
    
    list_display = [
        'user', 'code_masked', 'is_valid_display', 'used',
        'created_at', 'expires_at', 'ip_address'
    ]
    list_filter = ['used', 'created_at']
    search_fields = ['user__email', 'user__username', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def code_masked(self, obj):
        """Show masked OTP code for security"""
        return '***' + obj.code[-2:] if obj.code else '-'
    code_masked.short_description = 'Code'
    
    def is_valid_display(self, obj):
        """Show if OTP is currently valid"""
        if obj.used:
            return 'Used'
        elif obj.is_expired():
            return 'Expired'
        else:
            return 'Valid'
    is_valid_display.short_description = 'Status'


@admin.register(TrustedDevice)
class TrustedDeviceAdmin(admin.ModelAdmin):
    """Admin configuration for TrustedDevice model"""
    
    list_display = [
        'user', 'device_name', 'browser', 'os', 'ip_address',
        'is_active', 'last_used_at', 'expires_at'
    ]
    list_filter = ['is_active', 'device_type', 'last_used_at']
    search_fields = ['user__email', 'device_name', 'ip_address', 'location']
    ordering = ['-last_used_at']
    readonly_fields = ['created_at', 'last_used_at']
    
    actions = ['revoke_devices', 'extend_expiry']
    
    @admin.action(description='Revoke selected devices')
    def revoke_devices(self, request, queryset):
        count = 0
        for device in queryset:
            if device.is_active:
                device.revoke()
                count += 1
        self.message_user(request, f'{count} device(s) revoked.')
    
    @admin.action(description='Extend expiry by 30 days')
    def extend_expiry(self, request, queryset):
        count = 0
        for device in queryset:
            device.extend_expiry()
            count += 1
        self.message_user(request, f'{count} device(s) extended.')