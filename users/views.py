from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from inventory.models import Store
from .models import UserProfile

def is_admin(user):
    """Check if user is an admin/superuser"""
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def assign_store(request, user_id):
    """Assign a store to a staff member (admin only)"""
    user = get_object_or_404(User, id=user_id)
    
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Get active stores for selection
    stores = Store.objects.filter(is_active=True).order_by('name')
    
    if request.method == 'POST':
        store_id = request.POST.get('store')
        
        if store_id and store_id.isdigit():
            # Assign user to selected store
            store = get_object_or_404(Store, id=store_id)
            user_profile.store = store
            user_profile.save()
            messages.success(request, f"{user.username} has been assigned to {store.name}")
        else:
            # Remove store assignment (global access)
            user_profile.store = None
            user_profile.save()
            messages.success(request, f"{user.username} now has global access (no store restriction)")
        
        return redirect('admin:auth_user_changelist')
    
    return render(request, 'users/assign_store.html', {
        'user': user,
        'user_profile': user_profile,
        'stores': stores,
    })

@login_required
def current_user_store(request):
    """Display the current user's store assignment"""
    if hasattr(request.user, 'profile') and request.user.profile.store:
        store = request.user.profile.store
        return render(request, 'users/user_store.html', {
            'store': store,
        })
    else:
        messages.info(request, "You don't have a store assignment. Please contact an administrator.")
        return redirect('dashboard:index')