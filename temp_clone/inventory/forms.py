from django import forms
from django.forms import inlineformset_factory
from .models import Scooter, Parts, Store, StockTransfer, ScooterMaintenanceHistory, Supplier, Purchase, PurchaseItem

class ScooterForm(forms.ModelForm):
    class Meta:
        model = Scooter
        fields = '__all__'
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'last_maintenance': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class PartsForm(forms.ModelForm):
    class Meta:
        model = Parts
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'current_stock': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'e.g. 5 or 0.75 for liquids'}),
            'reorder_level': forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'e.g. 2 or 0.5 for liquids'}),
        }
        help_texts = {
            'current_stock': 'For liquids like oils, you can use decimal values (e.g., 0.75 for 750ml)',
            'reorder_level': 'Set the minimum level before reordering is needed',
        }

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = '__all__'

class StockTransferForm(forms.ModelForm):
    class Meta:
        model = StockTransfer
        fields = ['source_store', 'destination_store', 'part', 'quantity', 
                 'transfer_date', 'status', 'notes']
        widgets = {
            'transfer_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'placeholder': 'Enter quantity (e.g., 5 or 0.75)'}),
        }
        help_texts = {
            'quantity': 'For liquids like oils, you can use decimal values (e.g., 0.75 for 750ml)',
            'part': 'Select the part to transfer',
            'source_store': 'Store where the part is currently located',
            'destination_store': 'Store where the part will be transferred to',
        }

class MaintenanceHistoryForm(forms.ModelForm):
    class Meta:
        model = ScooterMaintenanceHistory
        fields = ['scooter', 'maintenance_date', 'description', 'cost', 'performed_by', 'mileage_at_service']
        widgets = {
            'maintenance_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['invoice_number', 'supplier', 'invoice_date', 'due_date', 'status', 'total_amount', 'amount_paid', 'notes']
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ['store', 'part', 'description', 'quantity', 'unit_price']
        widgets = {
            'store': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'part': forms.Select(attrs={'class': 'form-control part-select', 'placeholder': 'Start typing part name or code...'}),
            'description': forms.TextInput(attrs={'placeholder': 'Item description', 'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make scooter field hidden
        if 'scooter' in self.fields:
            self.fields.pop('scooter')

# Create a formset for purchase items
PurchaseItemFormSet = inlineformset_factory(
    Purchase,
    PurchaseItem,
    form=PurchaseItemForm,
    extra=1,
    can_delete=True
)
