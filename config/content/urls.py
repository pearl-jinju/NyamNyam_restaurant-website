from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from .views import UploadFeed

# from config.settings import MEDIA_URL, MEDIA_ROOT


urlpatterns = [
    path('upload', UploadFeed.as_view())
]

print(urlpatterns)

# urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)