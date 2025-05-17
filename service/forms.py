from django import forms
from .models import JobCard, JobCardItem, ServiceChecklist
from django.contrib.auth import get_user_model
from inventory.models import Scooter, Parts

User = get_user_model()

class JobCardForm(forms.ModelForm):
    class Meta:
        model = JobCard
        fields = ['job_card_number', 'scooter', 'status', 'priority', 'description', 
                  'technician', 'mileage', 'estimated_completion', 'actual_completion',
                  'labor_hours', 'labor_rate', 'notes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'estimated_completion': forms.DateInput(attrs={'type': 'date'}),
            'actual_completion': forms.DateInput(attrs={'type': 'date'}),
            'labor_hours': forms.NumberInput(attrs={'step': '0.5', 'min': '0'}),
            'labor_rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter scooters to exclude those that are already in maintenance
        # unless this is an update to an existing job card
        if self.instance.pk is None:  # New job card
            self.fields['scooter'].queryset = Scooter.objects.exclude(status='maintenance')
        
        # Set initial job card number if not provided
        if not self.instance.pk and not self.initial.get('job_card_number'):
            # Get the last job card number and increment it
            last_job_card = JobCard.objects.order_by('-job_card_number').first()
            if last_job_card and last_job_card.job_card_number.startswith('JC'):
                try:
                    number = int(last_job_card.job_card_number[2:]) + 1
                    self.initial['job_card_number'] = f'JC{number:06d}'
                except ValueError:
                    self.initial['job_card_number'] = 'JC000001'
            else:
                self.initial['job_card_number'] = 'JC000001'

class JobCardItemForm(forms.ModelForm):
    class Meta:
        model = JobCardItem
        fields = ['part', 'quantity', 'unit_price', 'total_price']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01', 'class': 'part-quantity'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'part-price', 'readonly': 'readonly'}),
            'total_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'part-total', 'readonly': 'readonly'}),
        }
        help_texts = {
            'quantity': 'Enter decimal values (e.g., 1.5) for items like oil measured in liters',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show parts that have stock available
        self.fields['part'].queryset = Parts.objects.filter(current_stock__gt=0)
        
        # If we have an instance with a part, get its price
        if self.instance.pk and self.instance.part:
            self.initial['unit_price'] = self.instance.part.unit_price

class ServiceChecklistForm(forms.ModelForm):
    class Meta:
        model = ServiceChecklist
        fields = ['item_name', 'is_checked', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
