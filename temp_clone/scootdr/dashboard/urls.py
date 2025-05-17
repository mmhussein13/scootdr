from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('logout/', views.custom_logout, name='custom_logout'),
]
