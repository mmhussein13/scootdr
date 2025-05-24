from django.db.models import Q

def filter_by_user_store(queryset, user):
    """
    Filter a queryset based on user's store assignment.
    
    Args:
        queryset: The queryset to filter
        user: The user object
        
    Returns:
        Filtered queryset
    """
    # Admin users can see all records
    if user.is_superuser or (user.is_staff and not hasattr(user, 'profile') or user.profile.store is None):
        return queryset
        
    # Regular staff can only see records from their assigned store
    if hasattr(user, 'profile') and user.profile.store:
        # Check if queryset model has a direct store field
        if hasattr(queryset.model, 'store'):
            return queryset.filter(store=user.profile.store)
        
        # For models with different relations to store
        if hasattr(queryset.model, 'scooter') and hasattr(queryset.model.scooter.field.related_model, 'store'):
            return queryset.filter(scooter__store=user.profile.store)
            
        if hasattr(queryset.model, 'part') and hasattr(queryset.model.part.field.related_model, 'store'):
            return queryset.filter(part__store=user.profile.store)
            
        # For transfer models that could involve source or destination store
        if hasattr(queryset.model, 'source_store') and hasattr(queryset.model, 'destination_store'):
            return queryset.filter(
                Q(source_store=user.profile.store) | Q(destination_store=user.profile.store)
            )
            
    # If no relevant store relation is found, return the original queryset
    # This is safer than returning nothing
    return queryset