#REST 호출이 가능하도록 설정
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from content.models import Feed, UserData
from user.models import User
from uuid import uuid4
import pandas as pd
from ast import literal_eval
from konlpy.tag import Hannanum
import os
from config.settings import MEDIA_ROOT
import re
from collections import Counter
from haversine import haversine


han = Hannanum()

# 위치 옮길것
def toVector(phrase, minmum_frequency=2, length_conditions=1):
    """
        빈도순으로 50개의 명사를 추출하는 함수
    """
    # 한글만 남기기
    new_phrase = re.sub(r"^[가-힣]", "", phrase)
    new_phrase = re.sub("([ㄱ-ㅎㅏ-ㅣ]+)", "", new_phrase)
    new_phrase = re.sub("([0-9])", "", new_phrase)
    # 일부 특수문자 제거
    new_phrase = re.sub(r"/.", "", new_phrase)
    # new_phrase = re.sub(r",", "", new_phrase)
    new_phrase = re.sub(r"_", "", new_phrase)
    new_phrase = re.sub(r"─", "", new_phrase)
    # 명사만 추출
    noun_list = han.nouns(new_phrase)
    # 명사 빈도수 
    noun_list_count = Counter(noun_list)

    # 빈도순 정렬
    main_noun_list_count = noun_list_count.most_common(200)
    # 길이가 2자 이상인 명사, 빈도수가 2회 이상인 단어만
    main_noun_list_count = [n[0] for n in main_noun_list_count if (len(n[0])>length_conditions) and (n[1]>=minmum_frequency)][:50]
    
    # # 명사 빈도수 딕셔너리 
    noun_dict_count = dict(noun_list_count)
    return [main_noun_list_count,noun_dict_count]

# Create your views here.
class Main(APIView):
    def get(self, request): 
        # DB 내 queryset 호출 
        # 원본 데이터
        feed_list = Feed.objects.all()  #select * from content_feed;
        feed_list = feed_list[6800:] #임시
        
        #데이터프레임으로 변환
        df =  pd.DataFrame(list(feed_list.values()))
        # 출력된 맛집 id만 출력
        feed_restaurant_id_list =  df['restaurant_id'].values
        
        # 유저 반영 데이터 가져오기
        user_data_list = UserData.objects.filter(restaurant_id__in=feed_restaurant_id_list)

        # 유저로그가 없는 경우
        if len(user_data_list)==0:
            
            # img_url 추출
            # 캐러셀로 구현을 위해 이미지 리스트를 넘겨줌
            df['img_url'] =  df['img_url'].apply(lambda x: literal_eval(x)) 
            
            # 맛집명이 공백이 있을경우, 캐러셀 작동 오류가 있으므로 맛집명의 공백을 _로 변경함
            df['name'] =  df['name'].apply(lambda x: x.replace(" ","_"))
            # vector 전처리
            df['vectors_1row'] =  df['vectors'].apply(lambda x: literal_eval(x)[:5])
            df['vectors_2row'] =  df['vectors'].apply(lambda x: literal_eval(x)[5:10])
            # 결과물 출력
            df = df.to_dict('records')

        # 유저 로그가 있는 경우
        else:
            # 필터링 된 유저로그를 데이터프레임으로 변환
            user_df =  pd.DataFrame(list(user_data_list.values())).reset_index(drop=True)
            
            # 필터링 된 유저 정보를 원본 데이터에 반영
            for idx_user_df in range(len(user_df)):
                # 식당명 추출
                name = user_df.loc[idx_user_df,'name']
                cond = df['name']==name
                # 이미지 리스트 변경
                # 이미지 리스트 불러오기
                user_img = literal_eval(user_df.loc[idx_user_df,'img_url'])[0]
             
                # 출력값 리스트화 후 값 추출
                new_img_list = literal_eval(df.loc[cond,'img_url'].values[0])
                new_img_list.append(user_img)
                # 중복값 제거
                new_img_list = list(set(new_img_list))

                df.loc[cond,'img_url'] = str(new_img_list)
                # vector 변경
                user_comment = user_df.loc[idx_user_df,'comment']
                
                new_comment =  df.loc[cond,'comment'].values[0] +" " + user_comment
                new_vectors = list(toVector(new_comment)[0])
                df.loc[cond,'vectors'] = str(new_vectors)
            # 딕셔너리 점수 반영
            
            
            
            # img_url 추출
            # 캐러셀로 구현을 위해 이미지 리스트를 넘겨줌
            df['img_url'] =  df['img_url'].apply(lambda x: " ".join(literal_eval(str(x))).split(" "))
            
            # 맛집명이 공백이 있을경우, 캐러셀 작동 오류가 있으므로 맛집명의 공백을 _로 변경함
            df['name'] =  df['name'].apply(lambda x: x.replace(" ","_"))
            # vector 전처리
            df['vectors_1row'] =  df['vectors'].apply(lambda x: literal_eval(x)[:5])
            df['vectors_2row'] =  df['vectors'].apply(lambda x: literal_eval(x)[5:10]) 

            # 결과물 출력
            df = df.to_dict('records')
                

        # 세션 정보 받아오기
        # 로그인 관련 정보 출력
        email = request.session.get('email', None)
        
        # 세션정보가 없는경우
        if email is None:
            return render(request,"user/login.html") #context html로 넘길것
        
        # # 세션 정보가 입력된 경우 데이터 가져오기       
        user = User.objects.filter(email=email).first()
        
        # # 회원 정보가 다르다면?
        if user is None:
            return render(request,"user/login.html") #context html로 넘길것 
        
        # # 세션정보가 있는 상태에서만 main 창을 보여줄것
        return render(request,"nyam\main.html", context=dict(feeds=df, user=user)) #context html로 넘길것

    def post(self, request):
        print("POST")
        return render(request,"nyam\main.html")
    
    
class MainFeed(APIView):
    def get(self, request): 
        # 쿼리 받아오기
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        
        curr_latitude = float(latitude)
        curr_longitude = float(longitude)
        
        print(curr_latitude,curr_longitude)
        
        # DB 내 queryset 호출 
        # 원본 데이터
        feed_list = Feed.objects.all()  #select * from content_feed;
        
        #데이터프레임으로 변환
        df =  pd.DataFrame(list(feed_list.values()))
        
        
        # 한국 데이터만 가져온다.
        cond = ((df['latitude'] >= 32)&(44 >= df['latitude'])) | ((df['longitude']>=123) & (133 >= df['longitude']))
        df = df[cond]
        
        # 현재 위치기준 거리별 정렬 
        df['distance'] = df.apply(lambda x: int(haversine((curr_latitude, curr_longitude),(float(x['latitude']), float(x['longitude'])), unit='km')),axis=1 ) 
        
        # 주변거리 기준 필터링(10km 이내)
        df = df[df['distance']<15]
        df = df.sort_values(by='distance')
        # 100개 이내로 추출
        df = df.iloc[:100,:]
        
        
        
        # 출력된 맛집 id만 출력
        feed_restaurant_id_list =  df['restaurant_id'].values
        
        # 유저 반영 데이터 가져오기
        user_data_list = UserData.objects.filter(restaurant_id__in=feed_restaurant_id_list)

        # 유저로그가 없는 경우
        if len(user_data_list)==0:
            
            # img_url 추출
            # 캐러셀로 구현을 위해 이미지 리스트를 넘겨줌
            df['img_url'] =  df['img_url'].apply(lambda x: literal_eval(x)) 
            
            # 맛집명이 공백이 있을경우, 캐러셀 작동 오류가 있으므로 맛집명의 공백을 _로 변경함
            df['name'] =  df['name'].apply(lambda x: x.replace(" ","_"))
            # vector 전처리
            df['vectors_1row'] =  df['vectors'].apply(lambda x: literal_eval(x)[:5])
            df['vectors_2row'] =  df['vectors'].apply(lambda x: literal_eval(x)[5:10])
            # # 결과물 출력
            df = df.to_dict('records')

        # 유저 로그가 있는 경우
        else:
            # 필터링 된 유저로그를 데이터프레임으로 변환
            user_df =  pd.DataFrame(list(user_data_list.values())).reset_index(drop=True)
            
            # 필터링 된 유저 정보를 원본 데이터에 반영
            for idx_user_df in range(len(user_df)):
                # 식당명 추출
                name = user_df.loc[idx_user_df,'name']
                cond = df['name']==name
                # 이미지 리스트 변경
                # 이미지 리스트 불러오기
                user_img = literal_eval(user_df.loc[idx_user_df,'img_url'])[0]
             
                # 출력값 리스트화 후 값 추출
                new_img_list = literal_eval(df.loc[cond,'img_url'].values[0])
                new_img_list.append(user_img)
                # 중복값 제거
                new_img_list = list(set(new_img_list))

                df.loc[cond,'img_url'] = str(new_img_list)
                # vector 변경
                user_comment = user_df.loc[idx_user_df,'comment']
                
                new_comment =  df.loc[cond,'comment'].values[0] +" " + user_comment
                new_vectors = list(toVector(new_comment)[0])
                df.loc[cond,'vectors'] = str(new_vectors)
            # 딕셔너리 점수 반영
            
            
            
            # img_url 추출
            # 캐러셀로 구현을 위해 이미지 리스트를 넘겨줌
            df['img_url'] =  df['img_url'].apply(lambda x: " ".join(literal_eval(str(x))).split(" "))
            
            # 맛집명이 공백이 있을경우, 캐러셀 작동 오류가 있으므로 맛집명의 공백을 _로 변경함
            df['name'] =  df['name'].apply(lambda x: x.replace(" ","_"))
            # vector 전처리
            df['vectors_1row'] =  df['vectors'].apply(lambda x: literal_eval(x)[:5])
            df['vectors_2row'] =  df['vectors'].apply(lambda x: literal_eval(x)[5:10]) 

            # 결과물 출력
            df = df.to_dict('records')
                
        
        
        # 세션 정보 받아오기
        # 로그인 관련 정보 출력
        email = request.session.get('email', None)
        
        # 세션정보가 없는경우
        if email is None:
            return render(request,"user/login.html") #context html로 넘길것
        
        # # 세션 정보가 입력된 경우 데이터 가져오기       
        user = User.objects.filter(email=email).first()
        
        # # 회원 정보가 다르다면?
        if user is None:
            return render(request,"user/login.html") #context html로 넘길것 
        


        # # 세션정보가 있는 상태에서만 main 창을 보여줄것
        return render(request,'nyam/main_feed.html',context=dict(mainfeeds=df)) #context html로 넘길것
        
        
    
    