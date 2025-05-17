from django.contrib import admin
from .models import ReportSchedule, SavedReport, Dashboard, DashboardWidget


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'frequency', 'next_run_date', 'is_active', 'created_by')
    list_filter = ('report_type', 'frequency', 'is_active')
    search_fields = ('name', 'description')
    date_hierarchy = 'next_run_date'


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_schedule', 'generated_by', 'date_generated', 'is_public')
    list_filter = ('is_public', 'date_generated')
    search_fields = ('title',)
    date_hierarchy = 'date_generated'


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_default', 'is_public', 'date_created')
    list_filter = ('is_default', 'is_public')
    search_fields = ('name', 'description', 'owner__username')


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'dashboard', 'widget_type', 'position_x', 'position_y', 'width', 'height')
    list_filter = ('widget_type', 'dashboard')
    search_fields = ('title', 'dashboard__name')