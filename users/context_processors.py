"""
Custom context processors for the users app.
These make commonly used data available to all templates.
"""

def user_store(request):
    """
    Make the user's assigned store available to all templates.
    
    This context processor adds:
    - user_store: The store object if the user has an assigned store
    - is_store_limited: Boolean indicating if user can only see one store
    """
    context = {
        'user_store': None,
        'is_store_limited': False
    }
    
    # Only proceed if user is authenticated
    if not request.user.is_authenticated:
        return context
    
    # Skip for superusers (they see all stores)
    if request.user.is_superuser:
        return context
    
    # Check if user has a profile with an assigned store
    if hasattr(request.user, 'profile') and request.user.profile.store:
        context['user_store'] = request.user.profile.store
        context['is_store_limited'] = True
    
    return context