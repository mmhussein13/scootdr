from django import forms
from .models import JobCard, JobCardItem, ServiceChecklist
from django.contrib.auth import get_user_model
from inventory.models import Scooter, Parts

User = get_user_model()

class JobCardForm(forms.ModelForm):
    class Meta:
        model = JobCard
        fields = ['job_card_number', 'scooter', 'store', 'status', 'priority', 'description', 
                  'technician', 'mileage', 'estimated_completion', 'actual_completion',
                  'labor_hours', 'labor_rate', 'notes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'estimated_completion': forms.DateInput(attrs={'type': 'date'}),
            'actual_completion': forms.DateInput(attrs={'type': 'date'}),
            'labor_hours': forms.NumberInput(attrs={'step': '0.5', 'min': '0'}),
            'labor_rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'scooter': forms.Select(attrs={
                'class': 'form-control select2-searchable',
                'placeholder': 'Type Number Plate or VIN to search...',
                'data-search-field': 'true'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        # Extract store parameter if provided
        store = kwargs.pop('store', None)
        
        super().__init__(*args, **kwargs)
        
        # Initialize base queryset excluding scooters in maintenance for new job cards
        if self.instance.pk is None:  # New job card
            base_queryset = Scooter.objects.exclude(status='maintenance')
        else:
            base_queryset = Scooter.objects.all()
            
        # Filter by store if provided
        if store:
            self.fields['scooter'].queryset = base_queryset.filter(store=store)
        else:
            self.fields['scooter'].queryset = base_queryset
        
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
        
        # Make the store field read-only if job card exists
        if self.instance.pk:
            self.fields['store'].widget.attrs['readonly'] = True
            self.fields['store'].widget.attrs['disabled'] = True
        
        # Add help text for fields
        self.fields['scooter'].help_text = "Type Number Plate or VIN to search for a scooter"
        self.fields['store'].help_text = "Select the store where the service is being performed"
        
        # If we have an existing instance or selected scooter, set the store
        if self.instance.pk and self.instance.scooter:
            self.initial['store'] = self.instance.scooter.store

class JobCardItemForm(forms.ModelForm):
    class Meta:
        model = JobCardItem
        fields = ['part', 'quantity', 'unit_price', 'total_price']
        widgets = {
            'part': forms.Select(attrs={
                'class': 'form-control select2-searchable part-select',
                'placeholder': 'Type Part Number or Name to search...',
                'data-search-field': 'true'
            }),
            'quantity': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01', 'class': 'part-quantity'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'part-price', 'readonly': 'readonly'}),
            'total_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'part-total', 'readonly': 'readonly'}),
        }
        help_texts = {
            'quantity': 'Enter decimal values (e.g., 1.5) for items like oil measured in liters',
            'part': 'Type Part Number or Name to search',
        }
    
    def __init__(self, *args, store=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter parts by store if provided and has stock available
        if store:
            self.fields['part'].queryset = Parts.objects.filter(store=store, current_stock__gt=0)
        else:
            # Only show parts that have stock available if no store specified
            self.fields['part'].queryset = Parts.objects.filter(current_stock__gt=0)
            
        # Update help text to reflect store filtering
        if store:
            self.fields['part'].help_text = f"Parts from {store.name} with available stock"
        
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
