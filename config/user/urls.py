from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from .views import Join, LogIn, LogOut
from config.settings import MEDIA_URL, MEDIA_ROOT


urlpatterns = [
    path('join', Join.as_view()),
    path('login', LogIn.as_view()),
    path('logout', LogOut.as_view())
    
]

urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)