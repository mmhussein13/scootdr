from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import JobCard, JobCardItem, ServiceChecklist
from inventory.models import Scooter, Parts, Store
from .forms import JobCardForm, JobCardItemForm, ServiceChecklistForm

@login_required
def job_card_list(request):
    # Use order_by to ensure newest job cards appear at the top
    job_cards_queryset = JobCard.objects.all().select_related('scooter', 'technician').order_by('-date_created')
    
    # Export to Excel if requested
    if 'export' in request.GET:
        from utils.export_utils import export_to_excel
        
        # Define columns for export: (field_name, display_name)
        columns = [
            ('job_card_number', 'Job Number'),
            ('scooter.vin', 'Scooter VIN'),
            ('scooter.make', 'Make'),
            ('scooter.model', 'Model'),
            ('description', 'Description'),
            ('reported_issue', 'Reported Issue'),
            ('technician.username', 'Technician'),
            ('status', 'Status'),
            ('priority', 'Priority'),
            ('date_created', 'Date Created'),
            ('scheduled_date', 'Scheduled Date'),
            ('actual_completion', 'Completion Date'),
            ('labor_hours', 'Labor Hours'),
            ('labor_rate', 'Labor Rate (R)'),
            ('total_cost', 'Total Cost (R)')
        ]
        
        return export_to_excel(
            data=job_cards_queryset,
            columns=columns,
            filename='Service_Job_Cards',
            title='Service Job Cards Report',
            sheet_name='Job Cards'
        )
    
    # Pagination - 9 items per page
    paginator = Paginator(job_cards_queryset, 9)
    page = request.GET.get('page')
    
    try:
        job_cards = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        job_cards = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        job_cards = paginator.page(paginator.num_pages)
    
    return render(request, 'service/job_card_list.html', {'job_cards': job_cards})

@login_required
def job_card_create(request):
    # Create a custom BaseInlineFormSet to pass store to the form
    class StoreFilteredInlineFormSet(BaseInlineFormSet):
        def __init__(self, *args, **kwargs):
            self.store = kwargs.pop('store', None)
            super().__init__(*args, **kwargs)
            
        def _construct_form(self, i, **kwargs):
            # Pass the store to each form in the formset
            kwargs['store'] = self.store
            return super()._construct_form(i, **kwargs)
    
    # Create the formset factory
    JobCardItemFormSet = inlineformset_factory(
        JobCard, JobCardItem, 
        form=JobCardItemForm, 
        extra=3, 
        can_delete=True,
        formset=StoreFilteredInlineFormSet
    )
    
    if request.method == 'POST':
        form = JobCardForm(request.POST)
        
        if form.is_valid():
            job_card = form.save(commit=False)
            
            # Store previous scooter status before changing it
            scooter = job_card.scooter
            job_card.previous_scooter_status = scooter.status
            
            # If the store wasn't set directly, use the scooter's store
            if not job_card.store:
                job_card.store = scooter.store
            
            if job_card.status == 'completed':
                # If completing right away, only change to available if not retired
                if scooter.status != 'retired':
                    scooter.status = 'available'
                scooter.last_maintenance = job_card.actual_completion
            else:
                # For any other status, set to maintenance
                scooter.status = 'maintenance'
            
            # Save the scooter with updated status
            scooter.save()
            
            # Save the job card to get an ID
            job_card.save()
            
            # Log successful job card creation
            print(f"Job Card created successfully with ID: {job_card.id}, Number: {job_card.job_card_number}, Store: {job_card.store}")
            
            # Re-instantiate the formset with the saved job_card instance and filtered by store
            formset = JobCardItemFormSet(request.POST, instance=job_card, store=job_card.store)
            
            if formset.is_valid():
                # Process parts and update inventory
                parts_valid = True
                parts_to_update = []
                
                for item_form in formset:
                    if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                        part = item_form.cleaned_data['part']
                        quantity = item_form.cleaned_data['quantity']
                        
                        # Check if part has enough stock
                        if part.current_stock >= quantity:
                            # Store part info for later update
                            parts_to_update.append((part, quantity))
                        else:
                            messages.error(request, f'Insufficient stock for {part.name}')
                            parts_valid = False
                            break
                
                if parts_valid:
                    # Update inventory and save formset
                    for part, quantity in parts_to_update:
                        part.current_stock -= quantity
                        part.save()
                    
                    # Save the formset items
                    formset.save()
                    
                    # Create default checklist items
                    default_items = [
                        "Brake inspection",
                        "Battery check",
                        "Tire pressure and condition",
                        "Lights and signals testing",
                        "Electrical system check",
                        "Frame and suspension inspection"
                    ]
                    
                    for item in default_items:
                        ServiceChecklist.objects.create(job_card=job_card, item_name=item)
                    
                    messages.success(request, 'Job card created successfully!')
                    
                    # Force a recalculation of the total cost
                    job_card.save()
                    
                    # Redirect to the job card list view after creating a job card
                    return redirect('service:job_card_list')
                else:
                    # If parts validation failed, delete the job card
                    job_card.delete()
                    # Restore original scooter status
                    scooter.status = job_card.previous_scooter_status
                    scooter.save()
                    # Error already shown
            else:
                # If formset is invalid, delete the job_card to prevent orphan records
                job_card.delete()
                # Restore original scooter status
                scooter.status = job_card.previous_scooter_status
                scooter.save()
                messages.error(request, 'There was an error with the job card items. Please check the form and try again.')
        else:
            formset = JobCardItemFormSet()  # Initialize formset
            messages.error(request, 'There was an error with the job card form. Please check and try again.')
    else:
        form = JobCardForm()
        # Handle AJAX request for filtered parts
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and 'store_id' in request.GET:
            store_id = request.GET.get('store_id')
            try:
                store = Store.objects.get(pk=store_id)
                # Filter parts by store (limit to 200 most recent for performance)
                parts = Parts.objects.filter(store=store, current_stock__gt=0).order_by('-id')[:200]
                # Filter scooters by store (limit to 100 most recent for performance)
                scooters = Scooter.objects.filter(store=store).exclude(status='maintenance').order_by('-id')[:100]
                
                return JsonResponse({
                    'success': True,
                    'parts': [{'id': p.id, 'text': f"{p.part_number} - {p.name} ({p.current_stock} in stock)", 'unit_price': float(p.unit_price)} for p in parts],
                    'scooters': [{'id': s.id, 'text': f"{s.number_plate} - {s.model} ({s.vin})"} for s in scooters],
                    'parts_count': Parts.objects.filter(store=store, current_stock__gt=0).count(),
                    'scooters_count': Scooter.objects.filter(store=store).exclude(status='maintenance').count()
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        # Check if store was selected        
        store_id = request.GET.get('store_id')
        store = None
        if store_id:
            try:
                store = Store.objects.get(pk=store_id)
            except Store.DoesNotExist:
                pass
                
        # Pass store to both form and formset for filtering
        form = JobCardForm(store=store)
        formset = JobCardItemFormSet(store=store)
    
    return render(request, 'service/job_card_form.html', {
        'form': form,
        'formset': formset,
        'stores': Store.objects.filter(is_active=True),
        'title': 'Create New Job Card'
    })

@login_required
def job_card_update(request, pk):
    job_card = get_object_or_404(JobCard, pk=pk)
    
    # Create a custom formset class to pass store to each form
    class UpdateStoreFilteredInlineFormSet(BaseInlineFormSet):
        def __init__(self, *args, **kwargs):
            self.store = kwargs.pop('store', None)
            super().__init__(*args, **kwargs)
            
        def _construct_form(self, i, **kwargs):
            # Pass the store to each form
            kwargs['store'] = self.store
            return super()._construct_form(i, **kwargs)
    
    JobCardItemFormSet = inlineformset_factory(
        JobCard, JobCardItem, 
        form=JobCardItemForm, 
        extra=1, 
        can_delete=True,
        formset=UpdateStoreFilteredInlineFormSet
    )
    
    if request.method == 'POST':
        form = JobCardForm(request.POST, instance=job_card)
        if form.is_valid():
            updated_job_card = form.save()
            
            # Pass the store to the formset
            formset = JobCardItemFormSet(request.POST, instance=updated_job_card, store=updated_job_card.store)
            if formset.is_valid():
                formset.save()
                
                # If job card is completed, update scooter status
                if updated_job_card.status == 'completed':
                    scooter = updated_job_card.scooter
                    # Only change to available if the scooter is not retired
                    if scooter.status != 'retired':
                        scooter.status = 'available'
                    scooter.last_maintenance = updated_job_card.actual_completion
                    scooter.save()
                
                messages.success(request, 'Job card updated successfully')
                return redirect('service:job_card_detail', pk=updated_job_card.pk)
    else:
        # Pass both the job_card instance and its store for filtering parts and scooters
        form = JobCardForm(instance=job_card, store=job_card.store)
        formset = JobCardItemFormSet(instance=job_card, store=job_card.store)
    
    return render(request, 'service/job_card_form.html', {
        'form': form,
        'formset': formset,
        'job_card': job_card,
        'title': 'Update Job Card'
    })

@login_required
def job_card_detail(request, pk):
    job_card = get_object_or_404(JobCard, pk=pk)
    parts_used = job_card.parts_used.all().select_related('part')
    checklist_items = job_card.checklist_items.all()
    
    context = {
        'job_card': job_card,
        'parts_used': parts_used,
        'checklist_items': checklist_items,
        'labor_cost': job_card.calculate_labor_cost(),
        'parts_cost': job_card.calculate_parts_cost(),
        'total_cost': job_card.total_cost
    }
    
    # Check if print view is requested
    if 'print' in request.GET:
        return render(request, 'service/job_card_print.html', context)
    
    return render(request, 'service/job_card_detail.html', context)

@login_required
def checklist_update(request, pk):
    job_card = get_object_or_404(JobCard, pk=pk)
    checklist_items = job_card.checklist_items.all()
    
    if request.method == 'POST':
        # Update checklist items
        for item in checklist_items:
            item_checked = request.POST.get(f'item_{item.id}', '') == 'on'
            item_notes = request.POST.get(f'notes_{item.id}', '')
            
            item.is_checked = item_checked
            item.notes = item_notes
            item.save()
        
        messages.success(request, 'Checklist updated successfully')
        return redirect('service:job_card_detail', pk=job_card.pk)
    
    return render(request, 'service/checklist_form.html', {
        'job_card': job_card,
        'checklist_items': checklist_items
    })

@login_required
def add_checklist_item(request, pk):
    job_card = get_object_or_404(JobCard, pk=pk)
    
    if request.method == 'POST':
        form = ServiceChecklistForm(request.POST)
        if form.is_valid():
            checklist_item = form.save(commit=False)
            checklist_item.job_card = job_card
            checklist_item.save()
            messages.success(request, 'Checklist item added successfully')
            return redirect('service:job_card_detail', pk=job_card.pk)
    else:
        form = ServiceChecklistForm()
    
    return render(request, 'service/checklist_item_form.html', {
        'form': form,
        'job_card': job_card
    })

def get_part_price(request, part_id):
    """AJAX endpoint to get a part's price"""
    try:
        part = Parts.objects.get(pk=part_id)
        return JsonResponse({
            'success': True,
            'price': float(part.unit_price)
        })
    except Parts.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Part not found'
        }, status=404)

@login_required
def job_card_delete(request, pk):
    job_card = get_object_or_404(JobCard, pk=pk)
    
    if request.method == 'POST':
        # Get all parts used in the job card before deleting it
        job_card_items = JobCardItem.objects.filter(job_card=job_card).select_related('part')
        
        # Return parts to inventory
        for item in job_card_items:
            part = item.part
            part.current_stock += item.quantity
            part.save()
            messages.info(request, f'Returned {item.quantity} units of {part.name} to inventory')
        
        # If the scooter is in maintenance status and the only job card for this scooter is being deleted,
        # update scooter status to available (unless it's retired)
        scooter = job_card.scooter
        other_active_job_cards = JobCard.objects.filter(
            scooter=scooter, 
            status__in=['pending', 'in_progress', 'on_hold']
        ).exclude(pk=job_card.pk).count()
        
        if other_active_job_cards == 0 and scooter.status == 'maintenance':
            # Check if the scooter was previously marked as retired
            # We can't simply check the current status since it's already 'maintenance'
            # So instead, check for the scooter model year. If it's very old, assume it's retired.
            # This is just a placeholder - in a real app, you'd have a 'is_retired' field
            # or some other way to track this permanent status.
            current_year = 2025  # Hard-coded current year
            if scooter.year < current_year - 10:  # Assuming scooters older than 10 years are retired
                messages.info(request, f'Scooter {scooter} remains in retired status')
            else:
                scooter.status = 'available'
                scooter.save()
                messages.info(request, f'Scooter {scooter} status updated to available')
        
        # Now delete the job card
        job_card.delete()
        messages.success(request, 'Job Card deleted successfully.')
        return redirect('service:job_card_list')
    
    return render(request, 'inventory/confirm_delete.html', {
        'object': job_card,
        'object_name': job_card.job_card_number,
        'title': 'Delete Job Card',
        'cancel_url': 'service:job_card_list'
    })
    
@login_required
def get_store_parts(request):
    """API endpoint to get parts available in a specific store"""
    try:
        store_id = request.GET.get('store_id')
        if not store_id:
            return JsonResponse({
                'success': False,
                'error': 'No store_id provided'
            })
            
        store = get_object_or_404(Store, pk=store_id)
        parts = Parts.objects.filter(store=store, current_stock__gt=0)
        
        parts_data = [
            {
                'id': part.id,
                'text': f"{part.part_number} - {part.name} ({part.current_stock} in stock)",
                'unit_price': float(part.unit_price),
                'current_stock': float(part.current_stock)
            }
            for part in parts
        ]
        
        return JsonResponse({
            'success': True,
            'parts': parts_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
