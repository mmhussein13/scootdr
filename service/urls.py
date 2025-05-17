from django.urls import path
from . import views

app_name = 'service'

urlpatterns = [
    path('job-card/', views.job_card_list, name='job_card_list'),
    path('job-card/add/', views.job_card_create, name='job_card_create'),
    path('job-card/<int:pk>/update/', views.job_card_update, name='job_card_update'),
    path('job-card/<int:pk>/detail/', views.job_card_detail, name='job_card_detail'),
    path('job-card/<int:pk>/delete/', views.job_card_delete, name='job_card_delete'),
    path('job-card/<int:pk>/checklist/', views.checklist_update, name='checklist_update'),
    path('job-card/<int:pk>/checklist/add/', views.add_checklist_item, name='add_checklist_item'),
    path('get-part-price/<int:part_id>/', views.get_part_price, name='get_part_price'),
]
