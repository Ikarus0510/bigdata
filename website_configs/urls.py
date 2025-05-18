from django.contrib import admin
from django.urls import path
from django.urls import include

urlpatterns = [
    
    path('topword/', include('app_top_keyword.urls')),
    
    path('topperson/', include('app_top_person.urls')),
   
    path('userkeyword/', include('app_user_keyword.urls')),

    path('voiceof/', include('app_voice_of.urls')),

    path('userkeyword_assoc/', include('app_user_keyword_association.urls')),

    path('news_multiangle/', include('app_news_multiangle.urls')),

    path('userkeyword_senti/', include('app_user_keyword_sentiment.urls')),

    path('taipei_recall/', include('app_taipei_recall.urls')),

    
    path('admin/', admin.site.urls),

    path('userkeyword_db/', include('app_user_keyword_db.urls')),

    path('top_person_db/', include('app_top_person_db.urls')),

    path('userkeyword_report/', include('app_user_keyword_llm_report.urls')),


]
