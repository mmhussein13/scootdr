from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Scooter URLs
    path('scooter/', views.scooter_list, name='scooter_list'),
    path('scooter/add/', views.scooter_create, name='scooter_create'),
    path('scooter/<int:pk>/update/', views.scooter_update, name='scooter_update'),
    path('scooter/<int:pk>/delete/', views.scooter_delete, name='scooter_delete'),
    path('scooter/<int:pk>/detail/', views.scooter_detail, name='scooter_detail'),
    
    # Parts URLs
    path('parts/', views.parts_list, name='parts_list'),
    path('parts/add/', views.parts_create, name='parts_create'),
    path('parts/<int:pk>/update/', views.parts_update, name='parts_update'),
    path('parts/<int:pk>/delete/', views.parts_delete, name='parts_delete'),
    
    # Store URLs
    path('store/', views.store_list, name='store_list'),
    path('store/add/', views.store_create, name='store_create'),
    path('store/<int:pk>/update/', views.store_update, name='store_update'),
    path('store/<int:pk>/delete/', views.store_delete, name='store_delete'),
    
    # Stock Transfer URLs
    path('stock-transfer/', views.stock_transfer_list, name='stock_transfer_list'),
    path('stock-transfer/add/', views.stock_transfer_create, name='stock_transfer_create'),
    path('stock-transfer/<int:pk>/update/', views.stock_transfer_update, name='stock_transfer_update'),
    path('stock-transfer/<int:pk>/delete/', views.stock_transfer_delete, name='stock_transfer_delete'),
    
    # Supplier URLs
    path('supplier/', views.supplier_list, name='supplier_list'),
    path('supplier/add/', views.supplier_create, name='supplier_create'),
    path('supplier/<int:pk>/update/', views.supplier_update, name='supplier_update'),
    path('supplier/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    path('supplier/<int:pk>/detail/', views.supplier_detail, name='supplier_detail'),
    
    # Purchase URLs
    path('purchase/', views.purchase_list, name='purchase_list'),
    path('purchase/add/', views.purchase_create, name='purchase_create'),
    path('purchase/<int:pk>/update/', views.purchase_update, name='purchase_update'),
    path('purchase/<int:pk>/delete/', views.purchase_delete, name='purchase_delete'),
    path('purchase/<int:pk>/detail/', views.purchase_detail, name='purchase_detail'),
    
    # API URLs for AJAX operations
    path('api/parts/<int:pk>/', views.part_detail_api, name='part_detail_api'),
    path('api/stores/<int:store_id>/parts/', views.store_parts_api, name='store_parts_api'),
]
