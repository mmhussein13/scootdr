from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='analytics_dashboard'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('rentals/', views.rental_report, name='rental_report'),
    path('maintenance/', views.maintenance_report, name='maintenance_report'),
    path('financial/', views.financial_report, name='financial_report'),
    path('customers/', views.customer_analysis, name='customer_analysis'),
    path('alerts/', views.alerts_dashboard, name='alerts_dashboard'),
    path('alerts/count/', views.alert_count_api, name='alert_count_api'),
    path('alerts/<int:alert_id>/acknowledge/', views.acknowledge_alert, name='acknowledge_alert'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    path('export/<str:report_type>/', views.export_report, name='export_report'),
]