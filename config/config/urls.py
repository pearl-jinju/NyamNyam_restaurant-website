"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from .views import Main, MainFeed, MainGuest, MainFeedGuest
from user.views import Join, LogIn
from .settings import MEDIA_URL, MEDIA_ROOT


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', MainGuest.as_view()),
    path('mainfeedguest/', MainFeedGuest.as_view()),
    path('main/', Main.as_view()),
    path('mainfeed/', MainFeed.as_view()),
    path('content/', include('content.urls')),  # api 경로 정의 , 실행할 앱 선택
    path('user/', include('user.urls')),
    path('main/join', Join.as_view()),
    path('main/login', LogIn.as_view()),
    ]

urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)