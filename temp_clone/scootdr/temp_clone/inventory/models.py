from django.db import models
from django.core.validators import MinValueValidator

class Store(models.Model):
    """Model representing a physical store location that holds inventory"""
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Supplier(models.Model):
    """Model representing a supplier for scooters and parts"""
    name = models.CharField(max_length=100)
    address = models.TextField()
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    payment_terms = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Scooter(models.Model):
    """Model representing a scooter in inventory"""
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('rented', 'Rented Out'),
        ('maintenance', 'Under Maintenance'),
        ('damaged', 'Damaged'),
        ('retired', 'Retired'),
    )
    
    vin = models.CharField(max_length=100, unique=True, verbose_name="VIN/Serial Number")
    license_number = models.CharField(max_length=100, unique=True, verbose_name="License Number", blank=True, null=True)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    color = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    daily_rate = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='scooters')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='scooters')
    purchase_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    mileage = models.PositiveIntegerField(default=0)
    last_maintenance = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.vin})"

class Parts(models.Model):
    """Model representing parts inventory"""
    part_number = models.CharField(max_length=100)  # Removed unique=True
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='parts')
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=5, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.CharField(max_length=100)
    location_in_store = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.part_number})"
    
    class Meta:
        verbose_name = "Part"
        verbose_name_plural = "Parts"
        # Make part number unique only within a store
        unique_together = ['part_number', 'store']

class StockTransfer(models.Model):
    """Model representing transfers of parts between stores"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    transfer_number = models.CharField(max_length=100, unique=True)
    source_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='outgoing_transfers')
    destination_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='incoming_transfers')
    part = models.ForeignKey(Parts, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    transfer_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Transfer #{self.transfer_number} - {self.part.name} ({self.quantity})"

class Purchase(models.Model):
    """Model representing purchases from suppliers (invoices)"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )
    
    invoice_number = models.CharField(max_length=100, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchases')
    invoice_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.supplier.name}"
    
    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid
    
    @property
    def payment_status_percent(self):
        if self.total_amount == 0:
            return 100
        return int((self.amount_paid / self.total_amount) * 100)

class PurchaseItem(models.Model):
    """Model representing items in a purchase invoice"""
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='purchase_items', null=True, blank=True)
    part = models.ForeignKey(Parts, on_delete=models.SET_NULL, null=True, blank=True)
    scooter = models.ForeignKey(Scooter, on_delete=models.SET_NULL, null=True, blank=True)  # Keeping for DB compatibility
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    def __str__(self):
        return f"{self.quantity} x {self.description}"
    
    @property
    def item_total(self):
        return self.quantity * self.unit_price

class ScooterMaintenanceHistory(models.Model):
    """Model representing maintenance history for scooters"""
    scooter = models.ForeignKey(Scooter, on_delete=models.CASCADE, related_name='maintenance_history')
    maintenance_date = models.DateField()
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    performed_by = models.CharField(max_length=100)
    mileage_at_service = models.PositiveIntegerField()
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Maintenance for {self.scooter} on {self.maintenance_date}"
    
    class Meta:
        verbose_name_plural = "Scooter maintenance histories"

class InventoryAlert(models.Model):
    """Model representing inventory alerts for low stock and other issues"""
    ALERT_TYPES = (
        ('low_stock', 'Low Stock'),
        ('overdue_rental', 'Overdue Rental'),
        ('maintenance_due', 'Maintenance Due'),
        ('expiring_item', 'Expiring Item'),
        ('price_change', 'Price Change')
    )
    
    SEVERITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    )
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed')
    )
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='new')
    
    # Related objects - one of these will be set depending on alert type
    part = models.ForeignKey(Parts, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    scooter = models.ForeignKey(Scooter, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, null=True, blank=True, related_name='alerts')
    
    # Contextual information
    threshold_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Notification metadata
    email_sent = models.BooleanField(default=False)
    dashboard_notification = models.BooleanField(default=True)
    
    # Audit fields
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='created_alerts')
    acknowledged_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    resolved_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    date_acknowledged = models.DateTimeField(null=True, blank=True)
    date_resolved = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_alert_type_display()}: {self.title}"
    
    class Meta:
        ordering = ['-severity', '-date_created']
