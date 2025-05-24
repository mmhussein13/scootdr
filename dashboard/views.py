from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.http import HttpResponseForbidden, JsonResponse
from functools import wraps

# Custom decorator to ensure only staff users can access dashboard pages
def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "You do not have permission to access the staff dashboard.")
            return redirect('landing:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
from django.db import models
from django.db.models import Count, Sum, Q, F
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.utils import timezone
from datetime import timedelta, datetime
import json
from inventory.models import Scooter, Parts, StockTransfer, Store, InventoryAlert
from inventory.utils import get_low_stock_items_for_dashboard, generate_inventory_alerts
from service.models import JobCard
from customers.models import Customer, Rental
from django.contrib import messages

@login_required
@staff_required
def dashboard(request):
    # Get store filter from request or set to 'all' as default
    store_filter = request.GET.get('store', 'all')
    
    # Generate inventory alerts if there are none (will check for duplicates internally)
    generate_inventory_alerts()
    
    # Get all alerts
    all_alerts_count = InventoryAlert.objects.exclude(status='resolved').count()
    
    # Get recent rentals with select_related for better performance - limit to 2 items
    recent_rentals = Rental.objects.select_related('customer', 'scooter').order_by('-start_date')[:2]
    
    # Get active rentals count
    active_rentals_count = Rental.objects.filter(status='active').count()
    
    # Get recent job cards with select_related for better performance - limit to 2 items
    recent_job_cards = JobCard.objects.select_related('scooter', 'technician').order_by('-date_created')[:2]
    
    # Get low stock alerts with select_related for better performance - limit to 2 items
    low_stock_alerts = Parts.objects.select_related('store').filter(
        current_stock__lte=models.F('reorder_level')
    ).order_by('current_stock')[:2]
    
    # Get formatted low stock items for the dashboard widget (limit to 2 as requested)
    low_stock_items_widget = get_low_stock_items_for_dashboard(limit=2)
    
    # Get low stock count for card display
    low_stock_count = Parts.objects.filter(current_stock__lte=models.F('reorder_level')).count()
    
    # Get recent stock transfers with select_related for better performance - limit to 2 items
    recent_stock_transfers = StockTransfer.objects.select_related(
        'source_store', 'destination_store', 'part'
    ).order_by('-transfer_date')[:2]
    
    # Get pending transfers count
    pending_transfers_count = StockTransfer.objects.filter(status='pending').count()
    
    # Get all stores for the dropdown
    stores = Store.objects.filter(is_active=True).order_by('name')
    
    # Base queryset for scooters
    scooter_queryset = Scooter.objects
    
    # Apply store filter if not 'all'
    if store_filter != 'all' and store_filter.isdigit():
        scooter_queryset = scooter_queryset.filter(store_id=store_filter)
    
    # Get counts for dashboard cards with the filtered queryset
    total_scooters = scooter_queryset.count()
    available_scooters = scooter_queryset.filter(status='available').count()
    unavailable_scooters = total_scooters - available_scooters
    
    # Get store-specific scooter counts
    store_scooter_data = []
    for store in stores:
        store_scooters = Scooter.objects.filter(store=store)
        total = store_scooters.count()
        available = store_scooters.filter(status='available').count()
        unavailable = total - available
        
        store_scooter_data.append({
            'id': store.id,
            'name': store.name,
            'total': total,
            'available': available,
            'unavailable': unavailable
        })
    
    total_customers = Customer.objects.count()
    active_job_cards = JobCard.objects.filter(status='in_progress').count()
    
    # Get rentals created in the last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_rentals_last_30_days = Rental.objects.filter(date_created__gte=thirty_days_ago).count()
    
    # Get new customers in the last 30 days
    new_customers_last_30_days = Customer.objects.filter(date_created__gte=thirty_days_ago).count()
    
    # CHART DATA
    
    # 1. Scooter Status Distribution Chart
    scooter_status_data = scooter_queryset.values('status').annotate(count=Count('status')).order_by('status')
    scooter_status_labels = [item['status'].capitalize() for item in scooter_status_data]
    scooter_status_counts = [item['count'] for item in scooter_status_data]
    
    # 2. Rental Trends by Month (Last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    rental_trends = Rental.objects.filter(
        start_date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    rental_trends_labels = [item['month'].strftime('%b %Y') for item in rental_trends]
    rental_trends_data = [item['count'] for item in rental_trends]
    
    # 3. Job Card Status Distribution
    job_card_status = JobCard.objects.values('status').annotate(count=Count('status')).order_by('status')
    job_card_status_labels = [item['status'].replace('_', ' ').capitalize() for item in job_card_status]
    job_card_status_counts = [item['count'] for item in job_card_status]
    
    # 4. Weekly Revenue from Rentals (Last 8 weeks)
    eight_weeks_ago = timezone.now() - timedelta(weeks=8)
    weekly_revenue = Rental.objects.filter(
        start_date__gte=eight_weeks_ago,
        status__in=['completed', 'active']
    ).annotate(
        week=TruncWeek('start_date')
    ).values('week').annotate(
        revenue=Sum('total_amount')
    ).order_by('week')
    
    weekly_revenue_labels = [item['week'].strftime('%d %b') for item in weekly_revenue]
    weekly_revenue_data = [float(item['revenue'] or 0) for item in weekly_revenue]
    
    # 5. Top 5 Most Rented Scooter Models
    top_rented_scooters = Rental.objects.values(
        'scooter__make', 'scooter__model'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    top_scooter_labels = [f"{item['scooter__make']} {item['scooter__model']}" for item in top_rented_scooters]
    top_scooter_data = [item['count'] for item in top_rented_scooters]
    
    # 6. Maintenance Job Cards by Month
    maintenance_trends = JobCard.objects.filter(
        date_created__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date_created')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    maintenance_labels = [item['month'].strftime('%b %Y') for item in maintenance_trends]
    maintenance_data = [item['count'] for item in maintenance_trends]
    
    context = {
        'recent_rentals': recent_rentals,
        'recent_job_cards': recent_job_cards,
        'low_stock_alerts': low_stock_alerts,
        'low_stock_items_widget': low_stock_items_widget,
        'all_alerts_count': all_alerts_count,
        'recent_stock_transfers': recent_stock_transfers,
        'total_scooters': total_scooters,
        'available_scooters': available_scooters,
        'unavailable_scooters': unavailable_scooters,
        'total_customers': total_customers,
        'active_job_cards': active_job_cards,
        'active_rentals_count': active_rentals_count,
        'low_stock_count': low_stock_count,
        'pending_transfers_count': pending_transfers_count,
        'new_rentals_last_30_days': new_rentals_last_30_days,
        'new_customers_last_30_days': new_customers_last_30_days,
        'stores': stores,
        'store_scooter_data': store_scooter_data,
        'current_store': store_filter,
        
        # Chart Data (JSON serialized)
        'scooter_status_chart': {
            'labels': json.dumps(scooter_status_labels),
            'data': json.dumps(scooter_status_counts)
        },
        'rental_trends_chart': {
            'labels': json.dumps(rental_trends_labels),
            'data': json.dumps(rental_trends_data)
        },
        'job_card_status_chart': {
            'labels': json.dumps(job_card_status_labels),
            'data': json.dumps(job_card_status_counts)
        },
        'weekly_revenue_chart': {
            'labels': json.dumps(weekly_revenue_labels),
            'data': json.dumps(weekly_revenue_data)
        },
        'top_scooter_chart': {
            'labels': json.dumps(top_scooter_labels),
            'data': json.dumps(top_scooter_data)
        },
        'maintenance_trends_chart': {
            'labels': json.dumps(maintenance_labels),
            'data': json.dumps(maintenance_data)
        }
    }
    
    return render(request, 'dashboard/index.html', context)

@login_required
@staff_required
def get_scooter_counts(request):
    """AJAX endpoint to get scooter counts by store"""
    store_id = request.GET.get('store_id', 'all')
    
    # Base queryset
    queryset = Scooter.objects
    
    # Apply store filter if not 'all'
    if store_id != 'all' and store_id.isdigit():
        queryset = queryset.filter(store_id=store_id)
    
    # Get counts
    total = queryset.count()
    available = queryset.filter(status='available').count()
    unavailable = total - available
    
    return JsonResponse({
        'total': total,
        'available': available,
        'unavailable': unavailable
    })

@login_required
@staff_required
def custom_logout(request):
    """
    Custom logout view to ensure proper redirection to landing page home
    """
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('landing:home')
