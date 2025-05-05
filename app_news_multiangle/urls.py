from django.urls import path
from app_news_multiangle import views

app_name = 'app_news_multiangle'

urlpatterns = [
    path('', views.home, name='home'),
    path('api_cluster_news/', views.api_cluster_news, name='api_cluster_news'),
]
