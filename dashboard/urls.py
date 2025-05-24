from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('api/scooter-counts/', views.get_scooter_counts, name='get_scooter_counts'),
]
