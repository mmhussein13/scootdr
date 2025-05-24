from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('assign-store/<int:user_id>/', views.assign_store, name='assign_store'),
    path('my-store/', views.current_user_store, name='my_store'),
]