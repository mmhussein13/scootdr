from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from inventory.models import Scooter

class Customer(models.Model):
    """Model representing a customer"""
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(validators=[phone_regex], max_length=17)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    driver_license = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField()
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_active_rentals(self):
        return self.rentals.filter(end_date__isnull=True)

class Rental(models.Model):
    """Model representing a scooter rental"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue'),
    )
    
    rental_number = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='rentals')
    scooter = models.ForeignKey(Scooter, on_delete=models.CASCADE, related_name='rentals')
    start_date = models.DateTimeField()
    expected_end_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    rate_type = models.CharField(max_length=20, choices=[('hourly', 'Hourly'), ('daily', 'Daily')])
    rate_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    deposit_returned = models.BooleanField(default=False)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    mileage_start = models.PositiveIntegerField()
    mileage_end = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Rental #{self.rental_number} - {self.customer} - {self.scooter}"
    
    def calculate_total(self):
        """Calculate the total amount based on rate and duration"""
        if self.end_date:
            from django.utils import timezone
            from datetime import timedelta
            
            duration = self.end_date - self.start_date
            
            if self.rate_type == 'hourly':
                # Calculate hours, rounding up
                hours = duration.total_seconds() / 3600
                hours = round(hours + 0.5)  # Round up to next hour
                return self.rate_amount * hours
            else:  # daily
                # Calculate days, rounding up
                days = duration.days
                if duration.seconds > 0:
                    days += 1  # Round up to next day
                return self.rate_amount * days
        return None
    
    def save(self, *args, **kwargs):
        # Set rental amount based on scooter rates
        if not self.pk:  # New rental
            if self.rate_type == 'hourly':
                self.rate_amount = self.scooter.hourly_rate
            else:
                self.rate_amount = self.scooter.daily_rate
            
            # Update scooter status to rented
            self.scooter.status = 'rented'
            self.scooter.save()
        
        # If rental is completed, calculate total and update scooter
        if self.end_date and self.status == 'completed':
            self.total_amount = self.calculate_total()
            
            # Update scooter status and mileage if completed
            self.scooter.status = 'available'
            if self.mileage_end:
                miles_used = self.mileage_end - self.mileage_start
                self.scooter.mileage += miles_used
            self.scooter.save()
        
        super().save(*args, **kwargs)

class PaymentMethod(models.Model):
    """Model representing a customer's payment method"""
    TYPE_CHOICES = (
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    )
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    card_number = models.CharField(max_length=16, blank=True)  # Last 4 digits only for security
    card_holder_name = models.CharField(max_length=100, blank=True)
    expiry_date = models.CharField(max_length=7, blank=True)  # MM/YYYY format
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.customer}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per customer
        if self.is_default:
            PaymentMethod.objects.filter(customer=self.customer, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class Payment(models.Model):
    """Model representing a payment for a rental"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    payment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment ${self.amount} for {self.rental}"
