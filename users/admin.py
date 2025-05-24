from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_store', 'assign_store_link')
    list_select_related = ('profile',)
    
    def get_store(self, instance):
        return instance.profile.store.name if instance.profile.store else 'All Stores'
    get_store.short_description = 'Assigned Store'
    
    def assign_store_link(self, obj):
        """Add a link to assign store to the user"""
        from django.urls import reverse
        from django.utils.html import format_html
        
        return format_html(
            '<a href="{}" class="button" style="white-space:nowrap;">'
            '<i class="fas fa-store"></i> Manage Store Access</a>',
            reverse('users:assign_store', args=[obj.id])
        )
    assign_store_link.short_description = 'Store Assignment'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(UserAdmin, self).get_inline_instances(request, obj)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)