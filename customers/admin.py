from django.contrib import admin
from .models import Customer, Rental, PaymentMethod, Payment

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'email', 'phone', 'city', 'is_active', 'date_created')
    list_filter = ('is_active', 'city', 'state', 'country')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'driver_license')
    date_hierarchy = 'date_created'

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('rental_number', 'customer', 'scooter', 'start_date', 'end_date', 'status', 'total_amount')
    list_filter = ('status', 'rate_type')
    search_fields = ('rental_number', 'customer__first_name', 'customer__last_name', 'scooter__vin')
    date_hierarchy = 'start_date'
    readonly_fields = ('total_amount',)

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('customer', 'payment_type', 'card_holder_name', 'is_default', 'is_active')
    list_filter = ('payment_type', 'is_default', 'is_active')
    search_fields = ('customer__first_name', 'customer__last_name', 'card_holder_name')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('rental', 'payment_method', 'amount', 'payment_date', 'status')
    list_filter = ('status', 'payment_date')
    search_fields = ('rental__rental_number', 'transaction_id')
    date_hierarchy = 'payment_date'
