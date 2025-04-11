from django.contrib import admin
from .models import DashboardSetting, Activity, Notification

@admin.register(DashboardSetting)
class DashboardSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'description', 'updated_at')
    search_fields = ('key', 'value', 'description')
    date_hierarchy = 'updated_at'

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'entity_type', 'entity_id', 'created_at', 'ip_address')
    list_filter = ('action', 'entity_type', 'created_at', 'user')
    search_fields = ('user__username', 'entity_type', 'entity_id', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'action', 'entity_type', 'entity_id', 'description', 'ip_address', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'user', 'is_read', 'is_global', 'created_at')
    list_filter = ('level', 'is_read', 'is_global', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    date_hierarchy = 'created_at' 