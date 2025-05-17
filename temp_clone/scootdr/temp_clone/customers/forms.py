from django import forms
from .models import Customer, Rental, PaymentMethod, Payment
from django.utils import timezone

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = ['rental_number', 'customer', 'scooter', 'start_date', 'expected_end_date', 
                 'rate_type', 'rate_amount', 'deposit_amount', 'status', 'mileage_start', 
                 'mileage_end', 'deposit_returned', 'notes']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expected_end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show available scooters for new rentals
        if not self.instance.pk:  # New rental
            self.fields['scooter'].queryset = self.fields['scooter'].queryset.filter(status='available')
            
            # Set initial rental number if not provided
            if not self.initial.get('rental_number'):
                # Get the last rental number and increment it
                from .models import Rental
                last_rental = Rental.objects.order_by('-rental_number').first()
                if last_rental and last_rental.rental_number.startswith('R'):
                    try:
                        number = int(last_rental.rental_number[1:]) + 1
                        self.initial['rental_number'] = f'R{number:06d}'
                    except ValueError:
                        self.initial['rental_number'] = 'R000001'
                else:
                    self.initial['rental_number'] = 'R000001'
            
            # Set initial dates
            now = timezone.now()
            self.initial['start_date'] = now.strftime('%Y-%m-%dT%H:%M')
            # Set expected end date to 24 hours from now
            self.initial['expected_end_date'] = (now + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')

class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['payment_type', 'card_number', 'card_holder_name', 'expiry_date', 'is_default', 'is_active']
        widgets = {
            'card_number': forms.TextInput(attrs={'maxlength': '4', 'placeholder': 'Last 4 digits only'}),
            'expiry_date': forms.TextInput(attrs={'placeholder': 'MM/YYYY'}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_method', 'amount', 'status', 'transaction_id', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        customer = kwargs.pop('customer', None)
        rental = kwargs.pop('rental', None)
        super().__init__(*args, **kwargs)
        
        # Only show payment methods for this customer
        if customer:
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(
                customer=customer, is_active=True)
            
            # If there's a default payment method, select it
            default_method = PaymentMethod.objects.filter(customer=customer, is_default=True, is_active=True).first()
            if default_method:
                self.initial['payment_method'] = default_method.pk
        
        # Set a default payment date
        self.initial['payment_date'] = timezone.now()
        
        # Set default status to completed
        self.initial['status'] = 'completed'
