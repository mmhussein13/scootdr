from django.contrib import admin
from .models import JobCard, JobCardItem, ServiceChecklist

class JobCardItemInline(admin.TabularInline):
    model = JobCardItem
    extra = 1

class ServiceChecklistInline(admin.TabularInline):
    model = ServiceChecklist
    extra = 1

@admin.register(JobCard)
class JobCardAdmin(admin.ModelAdmin):
    list_display = ('job_card_number', 'scooter', 'status', 'priority', 'technician', 'date_created', 'total_cost')
    list_filter = ('status', 'priority', 'technician')
    search_fields = ('job_card_number', 'scooter__vin', 'description')
    date_hierarchy = 'date_created'
    inlines = [JobCardItemInline, ServiceChecklistInline]
    readonly_fields = ('total_cost',)

@admin.register(JobCardItem)
class JobCardItemAdmin(admin.ModelAdmin):
    list_display = ('job_card', 'part', 'quantity', 'unit_price', 'total_price')
    list_filter = ('job_card__status',)
    search_fields = ('job_card__job_card_number', 'part__name')

@admin.register(ServiceChecklist)
class ServiceChecklistAdmin(admin.ModelAdmin):
    list_display = ('job_card', 'item_name', 'is_checked', 'date_updated')
    list_filter = ('is_checked', 'job_card__status')
    search_fields = ('job_card__job_card_number', 'item_name')
