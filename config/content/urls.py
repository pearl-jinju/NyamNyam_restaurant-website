from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from .views import UploadFeed, Profile, UploadProfile
from config.views import Main
from config.settings import MEDIA_URL, MEDIA_ROOT


urlpatterns = [
    path('upload', UploadFeed.as_view()),  
    path('profile', Profile.as_view()),
    path('profile/upload', UploadProfile.as_view()),
    path('main', Main.as_view()),
]


urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

