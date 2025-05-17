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
    path('', include('dashboard.urls')),
    path('inventory/', include('inventory.urls')),
    path('service/', include('service.urls')),
    path('customers/', include('customers.urls')),
    path('analytics/', include('analytics.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='login.html', next_page='login'), name='logout'),
    path('profile/', auth_views.TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('settings/', auth_views.TemplateView.as_view(template_name='settings.html'), name='settings'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
