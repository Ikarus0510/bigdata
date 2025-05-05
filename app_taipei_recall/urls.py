from django.urls import path
from app_taipei_recall import views

app_name='app_taipei_recall'

urlpatterns = [
    path('', views.home, name='home'),
    path('api_get_taipei_recall_data/', views.api_get_taipei_recall_data),
]
