#REST 호출이 가능하도록 설정
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from content.models import Feed
from uuid import uuid4
import pandas as pd
from ast import literal_eval
import os
from config.settings import MEDIA_ROOT


import re

# Create your views here.
class Main(APIView):
    def get(self, request):
        # DB 내 queryset 호출 
        feed_list = Feed.objects.all()  #select * from content_feed;
        feed_list = feed_list[6800:]
        #데이터프레임으로 변환
        df =  pd.DataFrame(list(feed_list.values()))
        
        # img_url 추출
        # 캐러셀로 구현을 위해 이미지 리스트를 넘겨줌
        df['img_url'] =  df['img_url'].apply(lambda x: " ".join(literal_eval(x)).split(" ")) 
        
        # 맛집명이 공백이 있을경우, 캐러셀 작동 오류가 있으므로 맛집명의 공백을 _로 변경함
        df['name'] =  df['name'].apply(lambda x: x.replace(" ","_"))
        # vector 전처리
        df['vectors_1row'] =  df['vectors'].apply(lambda x: " ".join(literal_eval(x)[:5])) 
        df['vectors_2row'] =  df['vectors'].apply(lambda x: " ".join(literal_eval(x)[5:10])) 
        # 결과물 출력
        df = df.to_dict('records')
        
        return render(request,"nyam\main.html", context=dict(feeds=df)) #context html로 넘길것

    def post(self, request):
        print("POST")
        return render(request,"nyam\main.html")
    
    