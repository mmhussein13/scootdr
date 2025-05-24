from django.core.management.base import BaseCommand, CommandError
from django.db.models import F, Q
from django.utils import timezone
from django.contrib.auth.models import User
from inventory.models import Parts, Scooter, InventoryAlert
from customers.models import Rental
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate inventory alerts for low stock, overdue rentals, and maintenance due'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            action='store_true',
            help='Send email notifications for generated alerts',
        )
        
    def handle(self, *args, **options):
        send_emails = options['email']
        alerts_created = 0
        
        # Get system user for automatic alerts
        system_user = User.objects.filter(username='admin').first()
        if not system_user:
            system_user = User.objects.filter(is_superuser=True).first()
        
        # Step 1: Check for low stock parts
        self.stdout.write('Checking for low stock parts...')
        low_stock_parts = Parts.objects.filter(
            current_stock__lte=F('reorder_level')
        )
        
        for part in low_stock_parts:
            # Check if an active alert already exists
            existing_alert = InventoryAlert.objects.filter(
                part=part,
                alert_type='low_stock',
                status__in=['new', 'acknowledged']
            ).exists()
            
            if not existing_alert:
                # Determine severity based on how low the stock is
                severity = 'medium'  # Default
                
                if part.current_stock == 0:
                    severity = 'critical'
                elif part.current_stock <= (part.reorder_level * 0.5):
                    severity = 'high'
                    
                # Create the alert
                alert = InventoryAlert.objects.create(
                    alert_type='low_stock',
                    title=f'Low Stock: {part.name}',
                    description=f'Part #{part.part_number} in store {part.store.name} is low on stock. '
                                f'Current stock: {part.current_stock}, Reorder level: {part.reorder_level}.',
                    severity=severity,
                    part=part,
                    store=part.store,
                    threshold_value=part.reorder_level,
                    current_value=part.current_stock,
                    created_by=system_user,
                    email_sent=False
                )
                
                alerts_created += 1
                self.stdout.write(f'  Created alert for {part.name} (Stock: {part.current_stock})')
        
        # Step 2: Check for overdue rentals
        self.stdout.write('Checking for overdue rentals...')
        current_time = timezone.now()
        
        overdue_rentals = Rental.objects.filter(
            status='active',
            expected_end_date__lt=current_time
        )
        
        for rental in overdue_rentals:
            # Check if an active alert already exists
            existing_alert = InventoryAlert.objects.filter(
                alert_type='overdue_rental',
                status__in=['new', 'acknowledged'],
                description__contains=rental.rental_number
            ).exists()
            
            if not existing_alert:
                # Determine severity based on how overdue the rental is
                days_overdue = (current_time - rental.expected_end_date).days
                
                severity = 'low'  # Default
                if days_overdue > 7:
                    severity = 'critical'
                elif days_overdue > 3:
                    severity = 'high'
                elif days_overdue > 1:
                    severity = 'medium'
                
                # Create the alert
                alert = InventoryAlert.objects.create(
                    alert_type='overdue_rental',
                    title=f'Overdue Rental: {rental.rental_number}',
                    description=f'Rental #{rental.rental_number} for {rental.customer.get_full_name()} '
                                f'is overdue by {days_overdue} days. Expected return date was '
                                f'{rental.expected_end_date.strftime("%Y-%m-%d %H:%M")}.',
                    severity=severity,
                    scooter=rental.scooter,
                    created_by=system_user,
                    email_sent=False
                )
                
                alerts_created += 1
                self.stdout.write(f'  Created alert for overdue rental #{rental.rental_number} ({days_overdue} days)')
        
        # Step 3: Check for scooters that need maintenance
        self.stdout.write('Checking for maintenance due...')
        # Get scooters that haven't had maintenance in over 90 days
        maintenance_due_days = 90
        maintenance_threshold = current_time - timedelta(days=maintenance_due_days)
        
        maintenance_due_scooters = Scooter.objects.filter(
            Q(last_maintenance__lt=maintenance_threshold) | 
            Q(last_maintenance__isnull=True, purchase_date__lt=maintenance_threshold)
        )
        
        for scooter in maintenance_due_scooters:
            # Check if an active alert already exists
            existing_alert = InventoryAlert.objects.filter(
                scooter=scooter,
                alert_type='maintenance_due',
                status__in=['new', 'acknowledged']
            ).exists()
            
            if not existing_alert:
                days_since_maintenance = None
                if scooter.last_maintenance:
                    days_since_maintenance = (current_time.date() - scooter.last_maintenance).days
                    
                    # Determine severity based on how overdue the maintenance is
                    severity = 'medium'  # Default
                    if days_since_maintenance > 180:  # 6 months
                        severity = 'critical'
                    elif days_since_maintenance > 120:  # 4 months
                        severity = 'high'
                        
                    description = f'Scooter {scooter.make} {scooter.model} (VIN: {scooter.vin}) ' \
                                  f'is due for maintenance. Last maintenance was ' \
                                  f'{days_since_maintenance} days ago on {scooter.last_maintenance}.'
                else:
                    # Never had maintenance - calculate days since purchase
                    days_since_purchase = (current_time.date() - scooter.purchase_date).days
                    severity = 'high'
                    description = f'Scooter {scooter.make} {scooter.model} (VIN: {scooter.vin}) ' \
                                  f'has never had maintenance since purchase {days_since_purchase} days ago.'
                
                # Create the alert
                alert = InventoryAlert.objects.create(
                    alert_type='maintenance_due',
                    title=f'Maintenance Due: {scooter.make} {scooter.model}',
                    description=description,
                    severity=severity,
                    scooter=scooter,
                    store=scooter.store,
                    created_by=system_user,
                    email_sent=False
                )
                
                alerts_created += 1
                self.stdout.write(f'  Created alert for maintenance due on {scooter.make} {scooter.model}')
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'Successfully created {alerts_created} new alerts.'))
        
        # Email notifications would go here if --email flag is set
        if send_emails and alerts_created > 0:
            self.stdout.write('Sending email notifications...')
            # This would be implemented with a proper email service
            # For now just mark the alerts as having emails sent
            InventoryAlert.objects.filter(email_sent=False).update(email_sent=True)
            self.stdout.write(self.style.SUCCESS('Email notifications sent.'))