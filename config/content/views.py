from django.shortcuts import render
from rest_framework.views import APIView
from .models import Feed
import pandas as pd

# Create your views here.
class Main(APIView):
    def get(self, request):
        # DB 내 queryset 호출 
        feed_list = Feed.objects.all()  #select * from content_feed;
        feed_list = feed_list[:2]
        #데이터프레임으로 변환
        df =  pd.DataFrame(list(feed_list.values()))
        # 결과물 출력
        df = df.to_dict('records')
        
        # df = pd.DataFrame(list(feed_list.values()))
        # feed_list = df.iloc[:2,:]
        # print(feed_list.values)
        return render(request,"nyam\main.html", context=dict(feeds=df)) #context html로 넘길것

    def post(self, request):
        print("POST")
        return render(request,"nyam\main.html")