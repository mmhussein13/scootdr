from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    # Customer URLs
    path('', views.customer_list, name='customer_list'),
    path('add/', views.customer_create, name='customer_create'),
    path('<int:pk>/update/', views.customer_update, name='customer_update'),
    path('<int:pk>/detail/', views.customer_detail, name='customer_detail'),
    path('<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    
    # Rental URLs
    path('rentals/', views.rental_list, name='rental_list'),
    path('rentals/add/', views.rental_create, name='rental_create'),
    path('rentals/<int:pk>/update/', views.rental_update, name='rental_update'),
    path('rentals/<int:pk>/detail/', views.rental_detail, name='rental_detail'),
    path('rentals/<int:pk>/complete/', views.rental_complete, name='rental_complete'),
    path('rentals/<int:pk>/delete/', views.rental_delete, name='rental_delete'),
    
    # Payment Method URLs
    path('<int:customer_id>/payment-method/add/', views.payment_method_create, name='payment_method_create'),
    path('payment-method/<int:pk>/update/', views.payment_method_update, name='payment_method_update'),
    
    # Payment URLs
    path('rentals/<int:rental_id>/payment/add/', views.payment_create, name='payment_create'),
]
