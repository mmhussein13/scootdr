"""
Utility functions for inventory management
"""
from django.db.models import F
from django.utils import timezone
from .models import Parts, Scooter, InventoryAlert


def check_for_low_stock_items():
    """
    Check for parts that are below their reorder level and create alerts
    Returns the number of new alerts created
    """
    # Find parts that are below reorder level
    low_stock_parts = Parts.objects.filter(current_stock__lte=F('reorder_level'))
    
    new_alerts_count = 0
    
    for part in low_stock_parts:
        # Check if there's already an active alert for this part
        existing_alert = InventoryAlert.objects.filter(
            part=part,
            alert_type='low_stock',
            status__in=['new', 'acknowledged']
        ).exists()
        
        if not existing_alert:
            # Create a new alert
            alert = InventoryAlert(
                alert_type='low_stock',
                title=f"Low Stock: {part.name}",
                description=f"Inventory level for {part.name} ({part.part_number}) is below reorder level. " \
                            f"Current stock: {part.current_stock}, Reorder level: {part.reorder_level}",
                severity='high' if part.current_stock == 0 else 'medium',
                part=part,
                store=part.store,
                threshold_value=part.reorder_level,
                current_value=part.current_stock,
                dashboard_notification=True
            )
            alert.save()
            new_alerts_count += 1
    
    return new_alerts_count


def check_for_maintenance_due():
    """
    Check for scooters that are due for maintenance based on mileage or time
    Returns the number of new alerts created
    """
    # Get scooters that haven't had maintenance in the last 90 days
    ninety_days_ago = timezone.now().date() - timezone.timedelta(days=90)
    
    # Either no maintenance record or last maintenance older than 90 days
    maintenance_due_scooters = Scooter.objects.filter(
        status__in=['available', 'rented'],
    ).filter(
        last_maintenance__lt=ninety_days_ago
    )
    
    new_alerts_count = 0
    
    for scooter in maintenance_due_scooters:
        # Check if there's already an active alert for this scooter
        existing_alert = InventoryAlert.objects.filter(
            scooter=scooter,
            alert_type='maintenance_due',
            status__in=['new', 'acknowledged']
        ).exists()
        
        if not existing_alert:
            # Create a new alert
            days_since_maintenance = (timezone.now().date() - scooter.last_maintenance).days if scooter.last_maintenance else 999
            
            alert = InventoryAlert(
                alert_type='maintenance_due',
                title=f"Maintenance Due: {scooter.make} {scooter.model}",
                description=f"Scooter {scooter.make} {scooter.model} ({scooter.vin}) is due for maintenance. " \
                            f"Last maintenance was {days_since_maintenance} days ago.",
                severity='high' if days_since_maintenance > 120 else 'medium',
                scooter=scooter,
                store=scooter.store,
                dashboard_notification=True
            )
            alert.save()
            new_alerts_count += 1
    
    return new_alerts_count


def generate_inventory_alerts():
    """
    Run all inventory alert checks and return total number of new alerts
    """
    total_alerts = 0
    
    # Check for low stock
    total_alerts += check_for_low_stock_items()
    
    # Check for maintenance due
    total_alerts += check_for_maintenance_due()
    
    return total_alerts


def get_low_stock_items_for_dashboard(limit=5):
    """
    Get low stock items for the dashboard widget
    Returns a list of parts with stock_percent calculated
    """
    low_stock_parts = Parts.objects.filter(
        current_stock__lte=F('reorder_level')
    ).select_related('store').order_by(
        'current_stock'
    )[:limit]
    
    # Prepare data for the template
    result = []
    for part in low_stock_parts:
        # Calculate percentage of current stock relative to reorder level
        if part.reorder_level > 0:
            stock_percent = min(100, int((part.current_stock / part.reorder_level) * 100))
        else:
            stock_percent = 0
            
        result.append({
            'id': part.id,
            'name': part.name,
            'part_number': part.part_number,
            'store': part.store,
            'current_stock': part.current_stock,
            'reorder_level': part.reorder_level,
            'stock_percent': stock_percent
        })
    
    return result