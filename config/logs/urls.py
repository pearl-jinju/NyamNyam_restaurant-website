from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from .views import SendLog
from config.settings import MEDIA_URL, MEDIA_ROOT


urlpatterns = [
    path('main/searchlog', SendLog.as_view()),
    path('searchlog', SendLog.as_view()),  

]


urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

