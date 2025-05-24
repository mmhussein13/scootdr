from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Avg, F, Q
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta, datetime
import json
import csv
import tempfile
import os

from inventory.models import Scooter, Parts, StockTransfer, Store, Purchase, PurchaseItem, InventoryAlert
from service.models import JobCard, JobCardItem
from customers.models import Customer, Rental, Payment
from .models import ReportSchedule, SavedReport, Dashboard, DashboardWidget


@login_required
def analytics_dashboard(request):
    """Main analytics dashboard view"""
    # Check if user has a custom default dashboard
    user_dashboards = Dashboard.objects.filter(owner=request.user)
    default_dashboard = user_dashboards.filter(is_default=True).first()
    
    if not default_dashboard and user_dashboards.exists():
        # If no default is set but dashboards exist, use the first one
        default_dashboard = user_dashboards.first()
    
    context = {
        'user_dashboards': user_dashboards,
        'default_dashboard': default_dashboard,
        'title': 'Analytics Dashboard'
    }
    
    if default_dashboard:
        context['widgets'] = default_dashboard.widgets.all().order_by('position_y', 'position_x')
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def inventory_report(request):
    """Inventory status and analytics report"""
    
    # Get overall inventory statistics
    total_parts = Parts.objects.count()
    total_value = Parts.objects.aggregate(total=Sum(F('current_stock') * F('unit_price')))['total'] or 0
    low_stock_count = Parts.objects.filter(current_stock__lte=F('reorder_level')).count()
    
    # Get parts by store
    parts_by_store = Store.objects.annotate(
        part_count=Count('parts'),
        inventory_value=Sum(F('parts__current_stock') * F('parts__unit_price'), default=0)
    ).order_by('-part_count')
    
    # Get top 10 most valuable parts
    top_value_parts = Parts.objects.annotate(
        total_value=F('current_stock') * F('unit_price')
    ).order_by('-total_value')[:10]
    
    # Get inventory value by category
    category_values = Parts.objects.values('category').annotate(
        total_value=Sum(F('current_stock') * F('unit_price'), default=0),
        part_count=Count('id')
    ).order_by('-total_value')
    
    context = {
        'title': 'Inventory Analytics',
        'total_parts': total_parts,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'parts_by_store': parts_by_store,
        'top_value_parts': top_value_parts,
        'category_values': category_values,
    }
    
    return render(request, 'analytics/inventory_report.html', context)


@login_required
def rental_report(request):
    """Rental performance and analytics report"""
    
    # Date range filters
    end_date = timezone.now()
    start_date = end_date - timedelta(days=90)  # Default to 90 days
    
    # Custom date range from request
    if request.GET.get('start_date') and request.GET.get('end_date'):
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)  # End of day
        except ValueError:
            messages.error(request, 'Invalid date format. Using default date range.')
    
    # Basic stats
    rentals_in_period = Rental.objects.filter(start_date__range=[start_date, end_date])
    total_rentals = rentals_in_period.count()
    total_revenue = rentals_in_period.aggregate(sum=Sum('total_amount'))['sum'] or 0
    
    # Rental status distribution
    status_distribution = rentals_in_period.values('status').annotate(count=Count('id'))
    
    # Revenue by scooter make/model
    revenue_by_scooter = rentals_in_period.values(
        'scooter__make', 'scooter__model'
    ).annotate(
        revenue=Sum('total_amount', default=0),
        rental_count=Count('id')
    ).order_by('-revenue')
    
    # Rentals by day of week
    rentals_by_day = rentals_in_period.annotate(
        day=F('start_date__week_day')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Convert day number to name
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for item in rentals_by_day:
        # Django's week_day is 1 (Sunday) to 7 (Saturday), adjusting to 0-6 for our array
        item['day_name'] = day_names[(item['day'] % 7) - 1]
    
    context = {
        'title': 'Rental Analytics',
        'start_date': start_date,
        'end_date': end_date,
        'total_rentals': total_rentals,
        'total_revenue': total_revenue,
        'status_distribution': status_distribution,
        'revenue_by_scooter': revenue_by_scooter,
        'rentals_by_day': rentals_by_day,
    }
    
    return render(request, 'analytics/rental_report.html', context)


@login_required
def maintenance_report(request):
    """Maintenance and service analytics report"""
    
    # Date range (default to last 90 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=90)
    
    # Job card statistics
    job_cards = JobCard.objects.filter(date_created__range=[start_date, end_date])
    total_jobs = job_cards.count()
    completed_jobs = job_cards.filter(status='completed').count()
    completion_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
    
    # Parts usage analysis
    parts_usage = JobCardItem.objects.filter(
        job_card__date_created__range=[start_date, end_date]
    ).values('part__name').annotate(
        count=Sum('quantity'),
        total_cost=Sum(F('quantity') * F('price'))
    ).order_by('-count')
    
    # Average job completion time
    job_duration = job_cards.filter(
        status='completed', 
        completion_date__isnull=False
    ).annotate(
        duration=F('completion_date') - F('date_created')
    ).aggregate(avg_duration=Avg('duration'))
    
    # The result is in days as a timedelta
    avg_days = job_duration['avg_duration'].days if job_duration['avg_duration'] else 0
    avg_hours = (job_duration['avg_duration'].seconds / 3600) if job_duration['avg_duration'] else 0
    
    # Job cards by priority
    jobs_by_priority = job_cards.values('priority').annotate(count=Count('id')).order_by('priority')
    
    context = {
        'title': 'Maintenance Analytics',
        'start_date': start_date,
        'end_date': end_date,
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'completion_rate': completion_rate,
        'parts_usage': parts_usage,
        'avg_duration_days': avg_days,
        'avg_duration_hours': avg_hours,
        'jobs_by_priority': jobs_by_priority,
    }
    
    return render(request, 'analytics/maintenance_report.html', context)


@login_required
def financial_report(request):
    """Financial performance report"""
    
    # Date range (default to last 12 months)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=365)
    
    # Monthly revenue from rentals
    monthly_revenue = Rental.objects.filter(
        start_date__range=[start_date, end_date]
    ).annotate(
        month=TruncMonth('start_date')
    ).values('month').annotate(
        revenue=Sum('total_amount', default=0)
    ).order_by('month')
    
    # Monthly expenses from purchases
    monthly_expenses = Purchase.objects.filter(
        invoice_date__range=[start_date, end_date]
    ).annotate(
        month=TruncMonth('invoice_date')
    ).values('month').annotate(
        expenses=Sum('total_amount', default=0)
    ).order_by('month')
    
    # Combine revenue and expenses by month
    financial_data = {}
    
    for item in monthly_revenue:
        month_key = item['month'].strftime('%Y-%m')
        if month_key not in financial_data:
            financial_data[month_key] = {
                'month_name': item['month'].strftime('%b %Y'),
                'revenue': 0,
                'expenses': 0,
                'profit': 0
            }
        financial_data[month_key]['revenue'] = item['revenue']
    
    for item in monthly_expenses:
        month_key = item['month'].strftime('%Y-%m')
        if month_key not in financial_data:
            financial_data[month_key] = {
                'month_name': item['month'].strftime('%b %Y'),
                'revenue': 0,
                'expenses': 0,
                'profit': 0
            }
        financial_data[month_key]['expenses'] = item['expenses']
    
    # Calculate profit and sort by month
    for month_key in financial_data:
        financial_data[month_key]['profit'] = financial_data[month_key]['revenue'] - financial_data[month_key]['expenses']
    
    # Convert to sorted list
    financial_summary = [financial_data[k] for k in sorted(financial_data.keys())]
    
    # Totals
    total_revenue = sum(item['revenue'] for item in financial_summary)
    total_expenses = sum(item['expenses'] for item in financial_summary)
    total_profit = total_revenue - total_expenses
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    context = {
        'title': 'Financial Analytics',
        'start_date': start_date,
        'end_date': end_date,
        'financial_summary': financial_summary,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
    }
    
    return render(request, 'analytics/financial_report.html', context)


@login_required
def export_report(request, report_type):
    """Export report data as CSV"""
    
    if report_type == 'inventory':
        # Inventory export
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Part Number', 'Name', 'Store', 'Category', 'Current Stock', 'Reorder Level', 'Unit Price', 'Total Value'])
        
        parts = Parts.objects.all().select_related('store')
        for part in parts:
            total_value = part.current_stock * part.unit_price
            writer.writerow([
                part.part_number,
                part.name,
                part.store.name,
                part.category,
                part.current_stock,
                part.reorder_level,
                part.unit_price,
                total_value
            ])
            
        return response
        
    elif report_type == 'rentals':
        # Rental export
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="rental_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Rental Number', 'Customer', 'Scooter', 'Start Date', 'End Date', 'Status', 'Total Amount'])
        
        rentals = Rental.objects.all().select_related('customer', 'scooter')
        for rental in rentals:
            writer.writerow([
                rental.rental_number,
                rental.customer.get_full_name(),
                f"{rental.scooter.make} {rental.scooter.model}",
                rental.start_date,
                rental.end_date or 'N/A',
                rental.get_status_display(),
                rental.total_amount
            ])
            
        return response
        
    else:
        messages.error(request, f"Export for {report_type} reports is not supported.")
        return redirect('analytics:analytics_dashboard')


@login_required
def alerts_dashboard(request):
    """Display and manage inventory alerts"""
    
    # Get alerts based on filter criteria
    alert_status = request.GET.get('status', 'new')  # Default to new alerts
    
    if alert_status == 'all':
        alerts = InventoryAlert.objects.all()
    else:
        alerts = InventoryAlert.objects.filter(status=alert_status)
    
    # Count by status for the sidebar
    alert_counts = InventoryAlert.objects.values('status').annotate(count=Count('id'))
    
    # Initialize with all possible statuses set to 0
    status_counts = {
        'new': 0,
        'acknowledged': 0,
        'resolved': 0,
        'dismissed': 0
    }
    
    # Update with actual counts
    for item in alert_counts:
        status_counts[item['status']] = item['count']
    
    # Count by type for charts
    alert_type_counts = {
        'low_stock': 0,
        'maintenance_due': 0,
        'overdue_rental': 0,
        'expiring_item': 0,
        'price_change': 0
    }
    
    alert_types = InventoryAlert.objects.values('alert_type').annotate(count=Count('id'))
    for item in alert_types:
        if item['alert_type'] in alert_type_counts:
            alert_type_counts[item['alert_type']] = item['count']
    
    context = {
        'title': 'Inventory Alerts',
        'alerts': alerts,
        'status_counts': status_counts,
        'alert_types': alert_types,
        'alert_type_counts': alert_type_counts,
        'current_status': alert_status,
    }
    
    return render(request, 'analytics/alerts_dashboard.html', context)


@login_required
def acknowledge_alert(request, alert_id):
    """Mark an alert as acknowledged"""
    if request.method == 'POST':
        alert = get_object_or_404(InventoryAlert, id=alert_id)
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        alert.date_acknowledged = timezone.now()
        alert.save()
        messages.success(request, 'Alert has been acknowledged.')
    
    return redirect('analytics:alerts_dashboard')


@login_required
def resolve_alert(request, alert_id):
    """Mark an alert as resolved"""
    if request.method == 'POST':
        alert = get_object_or_404(InventoryAlert, id=alert_id)
        alert.status = 'resolved'
        alert.resolved_by = request.user
        alert.date_resolved = timezone.now()
        alert.save()
        messages.success(request, 'Alert has been resolved.')
    
    return redirect('analytics:alerts_dashboard')


@login_required
def customer_analysis(request):
    """Customer segmentation and analytics"""
    
    # Basic customer statistics
    total_customers = Customer.objects.count()
    
    # Date range for new customers
    end_date = timezone.now()
    start_date = end_date - timedelta(days=365)  # Look at last year
    
    # New customers by month
    new_customers = Customer.objects.filter(
        date_created__range=[start_date, end_date]
    ).annotate(
        month=TruncMonth('date_created')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Get top customers by rental spend
    top_customers = Customer.objects.annotate(
        total_spent=Sum('rentals__total_amount', default=0),
        rental_count=Count('rentals')
    ).order_by('-total_spent')[:10]
    
    # Customer segmentation by rental frequency
    frequency_segments = {
        'new': Customer.objects.annotate(rental_count=Count('rentals')).filter(rental_count=1).count(),
        'occasional': Customer.objects.annotate(rental_count=Count('rentals')).filter(rental_count__range=[2, 5]).count(),
        'regular': Customer.objects.annotate(rental_count=Count('rentals')).filter(rental_count__range=[6, 15]).count(),
        'frequent': Customer.objects.annotate(rental_count=Count('rentals')).filter(rental_count__gt=15).count(),
    }
    
    context = {
        'title': 'Customer Analytics',
        'total_customers': total_customers,
        'new_customers': new_customers,
        'top_customers': top_customers,
        'frequency_segments': frequency_segments,
    }
    
    return render(request, 'analytics/customer_analysis.html', context)


@login_required
def alert_count_api(request):
    """API endpoint to get the count of active alerts"""
    # Count non-resolved alerts only
    alert_count = InventoryAlert.objects.exclude(status='resolved').count()
    
    return JsonResponse({'count': alert_count})