from django.http import HttpResponseForbidden
from django.conf import settings
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin


class StoreAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce store-based access control.
    Non-admin users can only view data from their assigned store.
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip for authentication/admin views or if user is not authenticated
        if not request.user.is_authenticated:
            return None
            
        # Skip for admin, static, or specifically excluded views
        if (request.path.startswith('/admin/') or 
            request.path.startswith('/static/') or
            request.path == '/' or
            request.path.startswith('/accounts/') or 
            request.path.startswith('/landing/')):
            return None
        
        # Admin users can access everything
        if request.user.is_superuser:
            return None
            
        # Get the URL pattern match to determine the app/view being accessed
        resolver_match = resolve(request.path)
        app_name = resolver_match.app_name
        
        # Some apps don't need store filtering
        if app_name in ['landing', 'dashboard', 'admin']:
            return None
        
        # Check if staff user has an assigned store
        try:
            user_profile = request.user.profile
            
            # Skip if staff and not assigned to any specific store (can see all)
            if request.user.is_staff and user_profile.store is None:
                return None
                
            # For GET requests, we'll filter in the view
            if request.method == 'GET':
                # Set the user's store ID in the request object for views to use
                if user_profile.store:
                    request.user_store_id = user_profile.store.id
                return None
                
            # For POST, PUT, DELETE, check if trying to access data from another store
            # This is a basic check that can be expanded upon for specific views
            store_id = view_kwargs.get('store_id') or request.POST.get('store_id')
            
            if store_id and user_profile.store and int(store_id) != user_profile.store.id:
                return HttpResponseForbidden("You do not have permission to access data from this store.")
                
        except Exception as e:
            # Log error but don't break access (fail safe)
            if settings.DEBUG:
                print(f"StoreAccessMiddleware error: {e}")
        
        return None