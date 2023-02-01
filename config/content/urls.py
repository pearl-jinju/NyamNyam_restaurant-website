from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from .views import UploadFeed, Profile, UploadProfile, ToggleLike, ToggleHate, ToggleBookmark
from config.views import Main
from config.settings import MEDIA_URL, MEDIA_ROOT


urlpatterns = [
    path('upload', UploadFeed.as_view()),  
    path('profile', Profile.as_view()),
    path('profile/upload', UploadProfile.as_view()),
    path('main', Main.as_view()),
    path('like', ToggleLike.as_view()),
    path('hate', ToggleHate.as_view()),
    path('bookmark', ToggleBookmark.as_view()),
]


urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

