from django.db import models
from django.contrib.auth.models import User


class ReportSchedule(models.Model):
    """Model for scheduling automated reports"""
    REPORT_TYPES = (
        ('inventory', 'Inventory Status'),
        ('sales', 'Sales Performance'),
        ('maintenance', 'Maintenance Summary'),
        ('rentals', 'Rental Activity'),
        ('financial', 'Financial Summary'),
        ('custom', 'Custom Report'),
    )
    
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    )
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    recipients = models.ManyToManyField(User, related_name='report_subscriptions')
    
    # Report customization
    include_charts = models.BooleanField(default=True)
    include_raw_data = models.BooleanField(default=True)
    date_range_days = models.PositiveIntegerField(default=30, help_text="Number of days to include in report")
    
    # Scheduling
    next_run_date = models.DateTimeField()
    last_run_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_reports')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"


class SavedReport(models.Model):
    """Model for storing generated reports"""
    title = models.CharField(max_length=200)
    report_schedule = models.ForeignKey(ReportSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='saved_reports')
    report_data = models.JSONField(help_text="JSON data containing report results")
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_reports')
    date_generated = models.DateTimeField(auto_now_add=True)
    
    # Access control
    is_public = models.BooleanField(default=False)
    allowed_users = models.ManyToManyField(User, related_name='accessible_reports', blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.date_generated.strftime('%Y-%m-%d')}"


class Dashboard(models.Model):
    """Model for customizable dashboards"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboards')
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class DashboardWidget(models.Model):
    """Model for widgets displayed on a dashboard"""
    WIDGET_TYPES = (
        ('chart', 'Chart'),
        ('stats', 'Statistics'),
        ('table', 'Data Table'),
        ('alert', 'Alert Summary'),
        ('kpi', 'KPI Indicator'),
    )
    
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    title = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    data_source = models.CharField(max_length=200, help_text="JSON path or API endpoint for widget data")
    config = models.JSONField(help_text="Widget configuration options")
    
    # Layout properties
    position_x = models.PositiveSmallIntegerField(default=0)
    position_y = models.PositiveSmallIntegerField(default=0)
    width = models.PositiveSmallIntegerField(default=1)
    height = models.PositiveSmallIntegerField(default=1)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} on {self.dashboard.name}"