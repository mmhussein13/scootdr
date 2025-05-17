from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Scooter, Parts, Store, StockTransfer, ScooterMaintenanceHistory, Supplier, Purchase, PurchaseItem
from .forms import (ScooterForm, PartsForm, StoreForm, StockTransferForm, MaintenanceHistoryForm,
                   SupplierForm, PurchaseForm, PurchaseItemForm, PurchaseItemFormSet)

# Scooter views
@login_required
def scooter_list(request):
    scooters_queryset = Scooter.objects.all().select_related('store')
    
    # Filter by status if specified
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        scooters_queryset = scooters_queryset.filter(status=status_filter)
    
    # Filter by category if specified
    category_filter = request.GET.get('category')
    if category_filter and category_filter != 'all':
        scooters_queryset = scooters_queryset.filter(category=category_filter)
    
    # Search by License No or VIN/Serial
    search_query = request.GET.get('search', '')
    if search_query:
        scooters_queryset = scooters_queryset.filter(
            license_number__icontains=search_query
        ) | scooters_queryset.filter(
            vin__icontains=search_query
        )
    
    # Export to Excel if requested
    if 'export' in request.GET:
        from utils.export_utils import export_to_excel
        
        # Define columns for export: (field_name, display_name)
        columns = [
            ('vin', 'VIN/Serial Number'),
            ('make', 'Make'),
            ('model', 'Model'),
            ('category', 'Category'),
            ('year', 'Year'),
            ('color', 'Color'),
            ('status', 'Status'),
            ('mileage', 'Mileage'),
            ('store.name', 'Store'),
            ('purchase_date', 'Purchase Date'),
            ('purchase_price', 'Purchase Price (R)'),
            ('last_maintenance', 'Last Maintenance'),
            ('notes', 'Notes')
        ]
        
        return export_to_excel(
            data=scooters_queryset,
            columns=columns,
            filename='Scooter_Inventory',
            title='Scooter Inventory Report',
            sheet_name='Scooters'
        )
    
    # Get all possible statuses for filter dropdown
    scooter_statuses = Scooter.STATUS_CHOICES
    
    # No pagination - all results are returned
    scooters = scooters_queryset
    
    return render(request, 'inventory/scooter_list.html', {
        'scooters': scooters, 
        'statuses': scooter_statuses,
        'current_status': status_filter or 'all',
        'current_category': category_filter or 'all',
        'search_query': search_query
    })

@login_required
def scooter_create(request):
    if request.method == 'POST':
        form = ScooterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Scooter added successfully.')
            return redirect('inventory:scooter_list')
    else:
        form = ScooterForm()
    
    return render(request, 'inventory/scooter_form.html', {'form': form, 'title': 'Add New Scooter'})

@login_required
def scooter_update(request, pk):
    scooter = get_object_or_404(Scooter, pk=pk)
    
    if request.method == 'POST':
        form = ScooterForm(request.POST, instance=scooter)
        if form.is_valid():
            form.save()
            messages.success(request, 'Scooter updated successfully.')
            return redirect('inventory:scooter_list')
    else:
        form = ScooterForm(instance=scooter)
    
    return render(request, 'inventory/scooter_form.html', {
        'form': form, 
        'title': 'Update Scooter',
        'scooter': scooter
    })

@login_required
def scooter_detail(request, pk):
    scooter = get_object_or_404(Scooter, pk=pk)
    maintenance_history = ScooterMaintenanceHistory.objects.filter(scooter=scooter).order_by('-maintenance_date')
    
    context = {
        'scooter': scooter,
        'maintenance_history': maintenance_history
    }
    
    return render(request, 'inventory/scooter_detail.html', context)

# Parts views
@login_required
def parts_list(request):
    # Get sort parameter from query string, default to 'part_number'
    sort_by = request.GET.get('sort', 'part_number')
    
    # Get store filter parameter from query string, default to None (all stores)
    store_id = request.GET.get('store', None)
    
    # Validate sort parameter to prevent injection
    valid_sort_fields = ['part_number', 'name', 'category', 'current_stock', 'reorder_level', 'unit_price']
    
    # Check if it's a reverse sort (descending)
    if sort_by.startswith('-') and sort_by[1:] in valid_sort_fields:
        sort_field = sort_by
    elif sort_by in valid_sort_fields:
        sort_field = sort_by
    else:
        # Default to part_number if invalid sort field
        sort_field = 'part_number'
    
    # Get all parts with sorting applied
    parts_query = Parts.objects.all().select_related('store')
    
    # Apply store filter if provided
    if store_id and store_id.isdigit():
        parts_query = parts_query.filter(store_id=int(store_id))
    
    # Search by Part Number or Name
    search_query = request.GET.get('search', '')
    if search_query:
        parts_query = parts_query.filter(
            part_number__icontains=search_query
        ) | parts_query.filter(
            name__icontains=search_query
        )
    
    # Apply sorting
    parts_queryset = parts_query.order_by(sort_field)
    
    # Get all stores for the store filter dropdown
    stores = Store.objects.all()
    
    # Export to Excel if requested
    if 'export' in request.GET:
        from utils.export_utils import export_to_excel
        
        # Define columns for export: (field_name, display_name)
        columns = [
            ('part_number', 'Part Number'),
            ('name', 'Name'),
            ('category', 'Category'),
            ('store.name', 'Store'),
            ('current_stock', 'Current Stock'),
            ('reorder_level', 'Reorder Level'),
            ('unit_price', 'Unit Price (R)'),
            ('location_in_store', 'Location in Store'),
            ('description', 'Description')
        ]
        
        return export_to_excel(
            data=parts_queryset,
            columns=columns,
            filename='Parts_Inventory',
            title='Parts Inventory Report',
            sheet_name='Parts'
        )
    
    # No pagination - return all results
    parts = parts_queryset
    
    # Pass the current sort field and store filter to the template context
    context = {
        'parts': parts,
        'current_sort': sort_field,
        'stores': stores,
        'selected_store_id': store_id if store_id and store_id.isdigit() else None,
        'search_query': search_query
    }
    
    return render(request, 'inventory/parts_list.html', context)

@login_required
def parts_create(request):
    if request.method == 'POST':
        form = PartsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Part added successfully.')
            return redirect('inventory:parts_list')
    else:
        form = PartsForm()
    
    return render(request, 'inventory/parts_form.html', {'form': form, 'title': 'Add New Part'})

@login_required
def parts_update(request, pk):
    part = get_object_or_404(Parts, pk=pk)
    
    if request.method == 'POST':
        form = PartsForm(request.POST, instance=part)
        if form.is_valid():
            form.save()
            messages.success(request, 'Part updated successfully.')
            return redirect('inventory:parts_list')
    else:
        form = PartsForm(instance=part)
    
    return render(request, 'inventory/parts_form.html', {
        'form': form, 
        'title': 'Update Part',
        'part': part
    })

# Store views
@login_required
def store_list(request):
    stores_queryset = Store.objects.all()
    
    # Pagination - 9 items per page
    paginator = Paginator(stores_queryset, 9)
    page = request.GET.get('page')
    
    try:
        stores = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        stores = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        stores = paginator.page(paginator.num_pages)
        
    return render(request, 'inventory/store_list.html', {'stores': stores})

@login_required
def store_create(request):
    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Store added successfully.')
            return redirect('inventory:store_list')
    else:
        form = StoreForm()
    
    return render(request, 'inventory/store_form.html', {'form': form, 'title': 'Add New Store'})

@login_required
def store_update(request, pk):
    store = get_object_or_404(Store, pk=pk)
    
    if request.method == 'POST':
        form = StoreForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, 'Store updated successfully.')
            return redirect('inventory:store_list')
    else:
        form = StoreForm(instance=store)
    
    return render(request, 'inventory/store_form.html', {
        'form': form, 
        'title': 'Update Store',
        'store': store
    })

# Stock Transfer views
@login_required
def stock_transfer_list(request):
    transfers_queryset = StockTransfer.objects.all().select_related('source_store', 'destination_store', 'part')
    
    # Export to Excel if requested
    if 'export' in request.GET:
        from utils.export_utils import export_to_excel
        
        # Define columns for export: (field_name, display_name)
        columns = [
            ('transfer_number', 'Transfer Number'),
            ('source_store.name', 'Source Store'),
            ('destination_store.name', 'Destination Store'),
            ('part.part_number', 'Part Number'),
            ('part.name', 'Part Name'),
            ('quantity', 'Quantity'),
            ('transfer_date', 'Transfer Date'),
            ('status', 'Status'),
            ('created_by.username', 'Created By'),
            ('notes', 'Notes')
        ]
        
        return export_to_excel(
            data=transfers_queryset,
            columns=columns,
            filename='Stock_Transfers',
            title='Stock Transfers Report',
            sheet_name='Transfers'
        )
    
    # Pagination - 9 items per page
    paginator = Paginator(transfers_queryset, 9)
    page = request.GET.get('page')
    
    try:
        transfers = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        transfers = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        transfers = paginator.page(paginator.num_pages)
    
    return render(request, 'inventory/stock_transfer_list.html', {'transfers': transfers})

@login_required
def stock_transfer_create(request):
    if request.method == 'POST':
        form = StockTransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.created_by = request.user
            
            # Auto-generate transfer number (format: TRF-YYYYMMDD-XXXX)
            from datetime import datetime
            import random
            date_str = datetime.now().strftime('%Y%m%d')
            random_num = ''.join([str(random.randint(0, 9)) for _ in range(4)])
            transfer.transfer_number = f"TRF-{date_str}-{random_num}"
            
            # Check if source store has enough stock
            part = form.cleaned_data['part']
            source_store = form.cleaned_data['source_store']
            quantity = form.cleaned_data['quantity']
            
            if part.store == source_store and part.current_stock >= quantity:
                # Update stock levels
                part.current_stock -= quantity
                part.save()
                
                transfer.save()
                messages.success(request, 'Stock transfer initiated successfully.')
                return redirect('inventory:stock_transfer_list')
            else:
                messages.error(request, 'Insufficient stock in source store.')
    else:
        form = StockTransferForm()
    
    return render(request, 'inventory/stock_transfer_form.html', {'form': form, 'title': 'Create Stock Transfer'})

@login_required
def stock_transfer_update(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk)
    old_status = transfer.status
    
    if request.method == 'POST':
        form = StockTransferForm(request.POST, instance=transfer)
        if form.is_valid():
            new_transfer = form.save(commit=False)
            
            # If status changed to completed, update destination store stock
            if old_status != 'completed' and new_transfer.status == 'completed':
                part = new_transfer.part
                
                # First check if the part with the same part number exists in the destination store
                try:
                    # Try to find the part with the SAME part number at the destination store
                    dest_part = Parts.objects.get(
                        part_number=part.part_number,
                        store=new_transfer.destination_store
                    )
                    # If found, update the stock but maintain all other attributes
                    dest_part.current_stock += new_transfer.quantity
                    
                    # Also ensure all other attributes match the source part 
                    # (in case they've been updated at the source)
                    dest_part.name = part.name
                    dest_part.description = part.description
                    dest_part.reorder_level = part.reorder_level
                    dest_part.unit_price = part.unit_price
                    dest_part.category = part.category
                    dest_part.location_in_store = part.location_in_store
                    
                    dest_part.save()
                except Parts.DoesNotExist:
                    # If not found, create a new part with the SAME part number
                    dest_part = Parts.objects.create(
                        part_number=part.part_number,  # Use the exact same part number
                        name=part.name,
                        description=part.description,
                        store=new_transfer.destination_store,
                        current_stock=new_transfer.quantity,
                        reorder_level=part.reorder_level,
                        unit_price=part.unit_price,
                        category=part.category,
                        location_in_store=part.location_in_store
                    )
            
            new_transfer.save()
            messages.success(request, 'Stock transfer updated successfully.')
            return redirect('inventory:stock_transfer_list')
    else:
        form = StockTransferForm(instance=transfer)
    
    return render(request, 'inventory/stock_transfer_form.html', {
        'form': form, 
        'title': 'Update Stock Transfer',
        'transfer': transfer
    })

# Supplier views
@login_required
def supplier_list(request):
    suppliers_queryset = Supplier.objects.all()
    
    # Export to Excel if requested
    if 'export' in request.GET:
        from utils.export_utils import export_to_excel
        
        # Define columns for export: (field_name, display_name)
        columns = [
            ('name', 'Supplier Name'),
            ('contact_person', 'Contact Person'),
            ('phone', 'Phone'),
            ('email', 'Email'),
            ('website', 'Website'),
            ('address', 'Address'),
            ('account_number', 'Account Number'),
            ('payment_terms', 'Payment Terms'),
            ('is_active', 'Active'),
            ('notes', 'Notes')
        ]
        
        return export_to_excel(
            data=suppliers_queryset,
            columns=columns,
            filename='Suppliers',
            title='Suppliers List',
            sheet_name='Suppliers'
        )
    
    # Pagination - 9 items per page
    paginator = Paginator(suppliers_queryset, 9)
    page = request.GET.get('page')
    
    try:
        suppliers = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        suppliers = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        suppliers = paginator.page(paginator.num_pages)
    
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier added successfully.')
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm()
    
    return render(request, 'inventory/supplier_form.html', {'form': form, 'title': 'Add New Supplier'})

@login_required
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supplier updated successfully.')
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'inventory/supplier_form.html', {
        'form': form, 
        'title': 'Update Supplier',
        'supplier': supplier
    })

@login_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    purchases = Purchase.objects.filter(supplier=supplier).order_by('-invoice_date')
    
    context = {
        'supplier': supplier,
        'purchases': purchases
    }
    
    return render(request, 'inventory/supplier_detail.html', context)

# Purchase views
@login_required
def purchase_list(request):
    purchases_queryset = Purchase.objects.all().select_related('supplier')
    
    # Export to Excel if requested
    if 'export' in request.GET:
        from utils.export_utils import export_to_excel
        
        # Define columns for export: (field_name, display_name)
        columns = [
            ('invoice_number', 'Invoice Number'),
            ('supplier.name', 'Supplier'),
            ('invoice_date', 'Invoice Date'),
            ('due_date', 'Due Date'),
            ('status', 'Status'),
            ('total_amount', 'Total Amount (R)'),
            ('amount_paid', 'Amount Paid (R)'),
            ('notes', 'Notes')
        ]
        
        return export_to_excel(
            data=purchases_queryset,
            columns=columns,
            filename='Purchases',
            title='Purchase Invoices',
            sheet_name='Invoices'
        )
    
    # Pagination - 9 items per page
    paginator = Paginator(purchases_queryset, 9)
    page = request.GET.get('page')
    
    try:
        purchases = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        purchases = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        purchases = paginator.page(paginator.num_pages)
    
    return render(request, 'inventory/purchase_list.html', {'purchases': purchases})

@login_required
def purchase_create(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.created_by = request.user
            purchase.save()
            
            # Process the formset
            formset = PurchaseItemFormSet(request.POST, instance=purchase)
            if formset.is_valid():
                purchase_items = formset.save(commit=False)
                
                # Update inventory levels for each purchased item
                for item in purchase_items:
                    if item.part and item.store:
                        # Update current stock of the part
                        item.part.current_stock += item.quantity
                        item.part.save()
                    
                    # Save the purchase item
                    item.save()
                
                # Save any deleted items from the formset
                formset.save()
                
                messages.success(request, 'Purchase invoice added successfully and inventory levels updated.')
                return redirect('inventory:purchase_list')
            else:
                # If formset is invalid, delete the purchase object and show errors
                purchase.delete()
                for error in formset.errors:
                    messages.error(request, error)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseForm()
        formset = PurchaseItemFormSet()
    
    return render(request, 'inventory/purchase_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Create Purchase Invoice'
    })

@login_required
def purchase_update(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    
    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            form.save()
            
            # Process the formset
            formset = PurchaseItemFormSet(request.POST, instance=purchase)
            if formset.is_valid():
                # Track items that are removed to adjust inventory
                original_items = {item.id: item for item in purchase.items.all()}
                
                # Save the updated formset items
                purchase_items = formset.save(commit=False)
                
                # Update inventory for existing items that changed quantities
                for item in purchase_items:
                    if item.id and item.id in original_items:
                        if item.part and item.store:
                            # Adjust inventory based on quantity difference
                            quantity_diff = item.quantity - original_items[item.id].quantity
                            if quantity_diff != 0:
                                item.part.current_stock += quantity_diff
                                item.part.save()
                    elif item.part and item.store:  # New item added
                        # Add new item's quantity to inventory
                        item.part.current_stock += item.quantity
                        item.part.save()
                    
                    # Save the purchase item
                    item.save()
                
                # Handle deleted items - reduce inventory
                for form in formset.deleted_forms:
                    item_id = form.instance.id
                    if item_id in original_items:
                        item = original_items[item_id]
                        if item.part and item.store:
                            # Remove deleted item quantity from inventory
                            item.part.current_stock -= item.quantity
                            if item.part.current_stock < 0:
                                item.part.current_stock = 0
                            item.part.save()
                
                # Save formset to handle deletions
                formset.save()
                
                messages.success(request, 'Purchase invoice updated successfully and inventory levels adjusted.')
                return redirect('inventory:purchase_list')
            else:
                for error in formset.errors:
                    messages.error(request, error)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseForm(instance=purchase)
        formset = PurchaseItemFormSet(instance=purchase)
    
    return render(request, 'inventory/purchase_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Update Purchase Invoice',
        'purchase': purchase
    })

# API views for AJAX calls
@login_required
def part_detail_api(request, pk):
    """API endpoint to get part details for AJAX requests"""
    try:
        part = get_object_or_404(Parts, pk=pk)
        data = {
            'id': part.id,
            'name': part.name,
            'part_number': part.part_number,
            'description': part.description,
            'unit_price': float(part.unit_price),
            'current_stock': float(part.current_stock),
            'category': part.category
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def store_parts_api(request, store_id):
    """API endpoint to get parts for a specific store"""
    try:
        parts = Parts.objects.filter(store_id=store_id)
        data = []
        for part in parts:
            data.append({
                'id': part.id,
                'name': part.name,
                'part_number': part.part_number,
                'current_stock': float(part.current_stock),
                'unit_price': float(part.unit_price)
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    items = purchase.items.all()
    
    context = {
        'purchase': purchase,
        'items': items
    }
    
    return render(request, 'inventory/purchase_detail.html', context)

# Delete views for each model
@login_required
def scooter_delete(request, pk):
    scooter = get_object_or_404(Scooter, pk=pk)
    
    if request.method == 'POST':
        scooter.delete()
        messages.success(request, 'Scooter deleted successfully.')
        return redirect('inventory:scooter_list')
    
    return render(request, 'inventory/confirm_delete.html', {
        'object': scooter,
        'object_name': f"{scooter.make} {scooter.model} ({scooter.vin})",
        'title': 'Delete Scooter',
        'cancel_url': 'inventory:scooter_list'
    })

@login_required
def parts_delete(request, pk):
    part = get_object_or_404(Parts, pk=pk)
    
    if request.method == 'POST':
        part.delete()
        messages.success(request, 'Part deleted successfully.')
        return redirect('inventory:parts_list')
    
    return render(request, 'inventory/confirm_delete.html', {
        'object': part,
        'object_name': f"{part.name} ({part.part_number})",
        'title': 'Delete Part',
        'cancel_url': 'inventory:parts_list'
    })

@login_required
def store_delete(request, pk):
    store = get_object_or_404(Store, pk=pk)
    
    if request.method == 'POST':
        store.delete()
        messages.success(request, 'Store deleted successfully.')
        return redirect('inventory:store_list')
    
    return render(request, 'inventory/confirm_delete.html', {
        'object': store,
        'object_name': store.name,
        'title': 'Delete Store',
        'cancel_url': 'inventory:store_list'
    })

@login_required
def stock_transfer_delete(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk)
    
    if request.method == 'POST':
        transfer.delete()
        messages.success(request, 'Stock transfer deleted successfully.')
        return redirect('inventory:stock_transfer_list')
    
    return render(request, 'inventory/confirm_delete.html', {
        'object': transfer,
        'object_name': transfer.transfer_number,
        'title': 'Delete Stock Transfer',
        'cancel_url': 'inventory:stock_transfer_list'
    })

@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Supplier deleted successfully.')
        return redirect('inventory:supplier_list')
    
    return render(request, 'inventory/confirm_delete.html', {
        'object': supplier,
        'object_name': supplier.name,
        'title': 'Delete Supplier',
        'cancel_url': 'inventory:supplier_list'
    })

@login_required
def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    
    if request.method == 'POST':
        # Adjust inventory levels by removing purchased quantities
        for item in purchase.items.all():
            if item.part and item.store:
                # Decrease inventory by the purchased quantity
                item.part.current_stock -= item.quantity
                # Ensure we don't go below zero
                if item.part.current_stock < 0:
                    item.part.current_stock = 0
                item.part.save()
        
        purchase.delete()
        messages.success(request, 'Purchase invoice deleted successfully and inventory levels adjusted.')
        return redirect('inventory:purchase_list')
    
    return render(request, 'inventory/confirm_delete.html', {
        'object': purchase,
        'object_name': purchase.invoice_number,
        'title': 'Delete Purchase Invoice',
        'warning': 'This will remove all purchased items from inventory. Are you sure you want to proceed?',
        'cancel_url': 'inventory:purchase_list'
    })
