from django.urls import path
from app_voice_of import views

app_name = 'app_voice_of'

urlpatterns = [
    path('', views.home, name='home'),
]