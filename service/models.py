from django.db import models
from django.core.validators import MinValueValidator
from inventory.models import Scooter, Parts

class JobCard(models.Model):
    """Model representing a service job card for scooter repairs/maintenance"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    job_card_number = models.CharField(max_length=100, unique=True)
    scooter = models.ForeignKey(Scooter, on_delete=models.CASCADE, related_name='job_cards')
    previous_scooter_status = models.CharField(max_length=20, blank=True, null=True, 
        help_text="The status of the scooter before maintenance")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    description = models.TextField()
    technician = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='job_cards')
    mileage = models.PositiveIntegerField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    estimated_completion = models.DateField(null=True, blank=True)
    actual_completion = models.DateField(null=True, blank=True)
    labor_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    labor_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Job Card #{self.job_card_number} - {self.scooter}"
    
    def calculate_parts_cost(self):
        """Calculate the cost of all parts used in this job"""
        return sum(item.total_price for item in self.parts_used.all())
    
    def calculate_labor_cost(self):
        """Calculate the labor cost"""
        return self.labor_hours * self.labor_rate
    
    def calculate_total_cost(self):
        """Calculate the total cost including parts and labor"""
        return self.calculate_parts_cost() + self.calculate_labor_cost()
    
    def save(self, *args, **kwargs):
        """Override save to update total cost"""
        # Only calculate costs if the instance already exists (has parts added)
        if self.pk:
            self.total_cost = self.calculate_total_cost()
        super().save(*args, **kwargs)

class JobCardItem(models.Model):
    """Model representing parts used in a job card"""
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='parts_used')
    part = models.ForeignKey(Parts, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.part.name} for {self.job_card}"
    
    def save(self, *args, **kwargs):
        """Override save to update total price and job card total"""
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Update job card total cost
        self.job_card.save()

class ServiceChecklist(models.Model):
    """Model representing checklist items for a job card"""
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='checklist_items')
    item_name = models.CharField(max_length=200)
    is_checked = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.item_name} for {self.job_card}"
