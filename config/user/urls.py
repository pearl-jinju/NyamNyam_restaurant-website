from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from .views import Join,Login


urlpatterns = [
    path('join', Join.as_view()),
    path('login', Login.as_view())
    
]
