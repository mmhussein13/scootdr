"""
URL configuration for scooterrentals project.
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Public-facing landing pages
    path('', include('landing.urls')),
    # Shopping cart
    path('cart/', include('cart.urls', namespace='cart')),
    # Staff dashboard (moved to /dashboard prefix)
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('inventory/', include('inventory.urls')),
    path('service/', include('service.urls')),
    path('customers/', include('customers.urls')),
    path('analytics/', include('analytics.urls')),
    path('users/', include('users.urls', namespace='users')),
    path('staff-login/', auth_views.LoginView.as_view(template_name='dashboard_login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing:home'), name='logout'),
    path('profile/', auth_views.TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('settings/', auth_views.TemplateView.as_view(template_name='settings.html'), name='settings'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
