from django.urls import path
from app_top_person import views

app_name="app_top_person"

urlpatterns = [
    
    path('', views.home, name='home'),

    path('api_get_topPerson/', views.api_get_topPerson),
]