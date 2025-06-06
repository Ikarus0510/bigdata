from django.urls import path
from app_user_keyword import views

app_name="app_user_keyword"

urlpatterns = [
    
    path('', views.home, name='home'),
    path('api_get_top_userkey/', views.api_get_top_userkey),

]

'''
# the first way:
The url path on the browser will be
http://localhost:8000/userkeyword/

# the second way:
The url path on the browser will be
http://localhost:8000/userkeyword/top_userkey/

The ajax url is as the following:
$.ajax({
    type: "POST",
    url: "api_get_top_userkey/",
'''
