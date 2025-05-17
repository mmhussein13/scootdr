from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    # Main navigation pages
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('buy/', views.buy, name='buy'),
    path('rent/', views.rent, name='rent'),
    path('restore/', views.restore, name='restore'),
    path('service/', views.service, name='service'),
    path('contact/', views.contact, name='contact'),
    
    # Account related pages
    path('account/', views.account, name='account'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset, name='password_reset'),
    
    # Additional pages
    path('terms/', views.terms, name='terms'),
    path('rental-terms/', views.rental_terms, name='rental_terms'),
    path('financing/', views.financing, name='financing'),
    path('maintenance-tips/', views.maintenance_tips, name='maintenance_tips'),
    path('restoration-gallery/', views.restoration_gallery, name='restoration_gallery'),
]