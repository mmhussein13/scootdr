from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import timedelta
from .models import Customer, Rental, PaymentMethod, Payment
from inventory.models import Scooter
from .forms import CustomerForm, RentalForm, PaymentMethodForm, PaymentForm

# Customer Views
@login_required
def customer_list(request):
    query = request.GET.get('q', '')
    
    if query:
        customers_queryset = Customer.objects.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query) | 
            Q(phone__icontains=query) |
            Q(driver_license__icontains=query)
        )
    else:
        customers_queryset = Customer.objects.all()
    
    # Pagination - 9 items per page
    paginator = Paginator(customers_queryset, 9)
    page = request.GET.get('page')
    
    try:
        customers = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        customers = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        customers = paginator.page(paginator.num_pages)
    
    return render(request, 'customers/customer_list.html', {'customers': customers, 'query': query})

@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, 'Customer added successfully.')
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm()
    
    return render(request, 'customers/customer_form.html', {'form': form, 'title': 'Add New Customer'})

@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer updated successfully.')
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, 'customers/customer_form.html', {
        'form': form, 
        'customer': customer,
        'title': 'Update Customer'
    })

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    # Get active rentals
    active_rentals = customer.rentals.filter(status='active')
    
    # Get rental history
    completed_rentals = customer.rentals.filter(status='completed')
    
    # Get payment methods
    payment_methods = customer.payment_methods.all()
    
    context = {
        'customer': customer,
        'active_rentals': active_rentals,
        'completed_rentals': completed_rentals,
        'payment_methods': payment_methods
    }
    
    return render(request, 'customers/customer_detail.html', context)

# Rental Views
@login_required
def rental_list(request):
    status_filter = request.GET.get('status', '')
    
    if status_filter:
        rentals_queryset = Rental.objects.filter(status=status_filter)
    else:
        rentals_queryset = Rental.objects.all()
    
    # Check for overdue rentals and update their status
    today = timezone.now()
    overdue_rentals = rentals_queryset.filter(status='active', expected_end_date__lt=today)
    overdue_rentals.update(status='overdue')
    
    # Get the queryset with all needed relations
    rentals_queryset = rentals_queryset.select_related('customer', 'scooter').order_by('-date_created')
    
    # Pagination - 9 items per page
    paginator = Paginator(rentals_queryset, 9)
    page = request.GET.get('page')
    
    try:
        rentals = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        rentals = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        rentals = paginator.page(paginator.num_pages)
    
    context = {
        'rentals': rentals,
        'status_filter': status_filter,
        'status_choices': Rental.STATUS_CHOICES
    }
    
    return render(request, 'customers/rental_list.html', context)

@login_required
def rental_create(request):
    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            rental = form.save(commit=False)
            
            # Ensure scooter is available
            scooter = rental.scooter
            if scooter.status != 'available':
                messages.error(request, f'Scooter {scooter} is not available for rent.')
                return redirect('customers:rental_create')
            
            rental.mileage_start = scooter.mileage
            rental.created_by = request.user
            rental.save()
            
            messages.success(request, 'Rental created successfully.')
            return redirect('customers:rental_detail', pk=rental.pk)
    else:
        # Only show available scooters
        form = RentalForm()
        form.fields['scooter'].queryset = Scooter.objects.filter(status='available')
    
    return render(request, 'customers/rental_form.html', {'form': form, 'title': 'Create New Rental'})

@login_required
def rental_update(request, pk):
    rental = get_object_or_404(Rental, pk=pk)
    
    if request.method == 'POST':
        form = RentalForm(request.POST, instance=rental)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rental updated successfully.')
            return redirect('customers:rental_detail', pk=rental.pk)
    else:
        form = RentalForm(instance=rental)
    
    return render(request, 'customers/rental_form.html', {
        'form': form, 
        'rental': rental,
        'title': 'Update Rental'
    })

@login_required
def rental_detail(request, pk):
    rental = get_object_or_404(Rental, pk=pk)
    payments = rental.payments.all()
    
    # Calculate payment stats
    total_paid = payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    balance_due = (rental.total_amount or 0) - total_paid
    
    context = {
        'rental': rental,
        'payments': payments,
        'total_paid': total_paid,
        'balance_due': balance_due
    }
    
    return render(request, 'customers/rental_detail.html', context)

@login_required
def rental_complete(request, pk):
    rental = get_object_or_404(Rental, pk=pk)
    
    if request.method == 'POST':
        mileage_end = request.POST.get('mileage_end')
        
        if not mileage_end:
            messages.error(request, 'Please enter the end mileage.')
            return redirect('customers:rental_detail', pk=rental.pk)
        
        try:
            mileage_end = int(mileage_end)
            if mileage_end < rental.mileage_start:
                messages.error(request, 'End mileage cannot be less than start mileage.')
                return redirect('customers:rental_detail', pk=rental.pk)
                
            rental.mileage_end = mileage_end
            rental.end_date = timezone.now()
            rental.status = 'completed'
            rental.save()
            
            messages.success(request, 'Rental completed successfully.')
            return redirect('customers:rental_detail', pk=rental.pk)
        except ValueError:
            messages.error(request, 'Invalid mileage value.')
            return redirect('customers:rental_detail', pk=rental.pk)
    
    return render(request, 'customers/rental_complete.html', {'rental': rental})

# Payment Method Views
@login_required
def payment_method_create(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            payment_method = form.save(commit=False)
            payment_method.customer = customer
            payment_method.save()
            
            messages.success(request, 'Payment method added successfully.')
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = PaymentMethodForm()
    
    return render(request, 'customers/payment_method_form.html', {
        'form': form, 
        'customer': customer,
        'title': 'Add Payment Method'
    })

@login_required
def payment_method_update(request, pk):
    payment_method = get_object_or_404(PaymentMethod, pk=pk)
    customer = payment_method.customer
    
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST, instance=payment_method)
        if form.is_valid():
            form.save()
            
            messages.success(request, 'Payment method updated successfully.')
            return redirect('customers:customer_detail', pk=customer.pk)
    else:
        form = PaymentMethodForm(instance=payment_method)
    
    return render(request, 'customers/payment_method_form.html', {
        'form': form, 
        'payment_method': payment_method,
        'customer': customer,
        'title': 'Update Payment Method'
    })

# Payment Views
@login_required
def payment_create(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    customer = rental.customer
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, customer=customer, rental=rental)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.rental = rental
            payment.payment_date = timezone.now()
            payment.save()
            
            messages.success(request, 'Payment processed successfully.')
            return redirect('customers:rental_detail', pk=rental.pk)
    else:
        # Calculate remaining balance
        total_paid = rental.payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        remaining = (rental.total_amount or 0) - total_paid
        
        form = PaymentForm(customer=customer, rental=rental, initial={'amount': remaining})
    
    return render(request, 'customers/payment_form.html', {
        'form': form, 
        'rental': rental,
        'customer': customer,
        'title': 'Process Payment'
    })

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully.')
        return redirect('customers:customer_list')
    
    return render(request, 'inventory/confirm_delete.html', {
        'object': customer,
        'object_name': customer.get_full_name(),
        'title': 'Delete Customer',
        'cancel_url': 'customers:customer_list'
    })

@login_required
def rental_delete(request, pk):
    rental = get_object_or_404(Rental, pk=pk)
    
    if request.method == 'POST':
        rental.delete()
        messages.success(request, 'Rental deleted successfully.')
        return redirect('customers:rental_list')
    
    return render(request, 'inventory/confirm_delete.html', {
        'object': rental,
        'object_name': rental.rental_number,
        'title': 'Delete Rental',
        'cancel_url': 'customers:rental_list'
    })
