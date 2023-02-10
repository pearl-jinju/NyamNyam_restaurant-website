#REST 호출이 가능하도록 설정
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from content.models import Feed, UserData, Like, Hate, Bookmark
from user.models import User
from uuid import uuid4
import pandas as pd
from ast import literal_eval
from konlpy.tag import Hannanum #, Okt
import os
from config.settings import MEDIA_ROOT, SECRET_API_KEY
import re
from collections import Counter
from haversine import haversine
import googlemaps

# # API키 입력
mykey = SECRET_API_KEY
maps = googlemaps.Client(key=mykey)  # my key값 입력
# 

# 주소 불러오는 함수
from geopy.geocoders import Nominatim
geo_local = Nominatim(user_agent='South Korea')


konlp = Hannanum()

# 불용어 리스트
file_path = "config/stopwords.txt"

with open(file_path, encoding='utf-8') as f:
    stopwords = f.read().splitlines()



# 위치 옮길것
def toVector(phrase, minmum_frequency=1, length_conditions=2, max_length_conditions=10):
    """
        빈도순으로 10개의 명사를 추출하는 함수
    """
    # 한글만 남기기
    new_phrase = re.sub("^[가-힣]", "", phrase)
    new_phrase = re.sub("([ㄱ-ㅎㅏ-ㅣ]+)", "", new_phrase)
    new_phrase = re.sub("([0-9])", "", new_phrase)
    # 일부 특수문자 제거
    new_phrase = re.sub("/.", "", new_phrase)
    new_phrase = re.sub("_", "", new_phrase)
    new_phrase = re.sub("─", "", new_phrase)
    # 명사만 추출
    noun_list = konlp.nouns(new_phrase)
   
    # 불용어/불건전한 단어 제거
    noun_list = [word for word in noun_list if not word in stopwords]
    
    # 명사 빈도수 
    noun_list_count = Counter(noun_list)

    # 빈도순 정렬
    main_noun_list_count = noun_list_count.most_common(10)
    # 길이가 2자 이상인 명사, 빈도수가 2회 이상인 단어만
    main_noun_list_count = [n[0] for n in main_noun_list_count if (len(n[0])>=length_conditions) and (n[1]>=minmum_frequency) and (len(n[0])<=max_length_conditions)][:10]
    
    # # 명사 빈도수 딕셔너리 
    noun_dict_count = dict(noun_list_count)
    return [main_noun_list_count,noun_dict_count]

def getLocationFromAddress(address,now_latitude,now_longitude):
    """쿼리로 입력된 주소를 위도 경도로 반환한다
    단, 주소 오류의 경우 상태를 출력하고 현재위치를 기준으로 탐색한다.

    Args:
        address (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        # 검색위치
        geo_location = maps.geocode(address)[0].get('geometry')

    except:
        curr_location = {"latitude": now_latitude, "longitude":now_longitude, "result":"fail"}
        return curr_location
        
    curr_location = {"latitude": geo_location['location']['lat'], "longitude":  geo_location['location']['lng'], "result":"success"}
    return curr_location




# Create your views here.
class MainGuest(APIView):
    def get(self, request): 
        # DB 내 queryset 호출 

        # 세션 정보 받아오기
        # 로그인 관련 정보 출력
        email = request.session.get('email', None)
        
        # 세션정보가 없는경우
        if email is None:
            return render(request,"nyam/main_guest.html") #context html로 넘길것
        
        # # 세션 정보가 입력된 경우 데이터 가져오기       
        user = User.objects.filter(email=email).first()
        
        # # 회원 정보가 없다면?
        if user is None:
            return render(request,"nyam/main_guest.html") #context html로 넘길것 
        return render(request,"nyam/main_guest.html") 
        
        # # # 세션정보가 있는 상태에서만 main 창을 보여줄것
        # return render(request,"nyam/main.html", context=dict( user=user)) #context html로 넘길것

    def post(self, request):
        pass
        # return render(request,"nyam/main.html")
        
class MainFeedGuest(APIView):
    def get(self, request): 
        # 쿼리 받아오기
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        tag = request.GET.get('tag')
        address = request.GET.get('address')
        name = request.GET.get('name')
        error= request.GET.get('error')
    
        
        # 검색어 체크
        search_keyword = ""
        if address!= "default":
            search_keyword = address
        if tag!= "default":
            search_keyword = tag
        if name!= "default":
            search_keyword = name

        
        # 검색어 적정성 확인 error는 error, correct로 나뉨
        if error =="error":
             return render(request,'nyam/search_guide.html',status=200) #context html로 넘길것               
        
        # 데이터 조회 시작
        
        # 주소 검색기능  ======================== ======================== ========================
        # 만약 주소값이 입력이 됐다면,
        if address!="default":
            curr_location = getLocationFromAddress(address,latitude, longitude)
            curr_latitude = float(curr_location['latitude'])
            curr_longitude = float(curr_location['longitude'])
            result = curr_location['result']
            
        # 만약 주소값이 입력되지 않았다면(= default)
        else:
            curr_latitude = float(latitude)
            curr_longitude = float(longitude)
            result = "sucess"
        
        
        # DB 내 모든 queryset 호출 
        feed_list = Feed.objects.all()  #select * from content_feed;

        #데이터프레임으로 변환
        df =  pd.DataFrame(list(feed_list.values()))
        
        #메모리 간소화
        del feed_list

        # 한국 데이터 필터링
        cond = ((df['latitude'] >= 32)&(44 >= df['latitude'])) | ((df['longitude']>=123) & (133 >= df['longitude']))
        df = df[cond]
        
        # 현재 위치기준 거리별 정렬 
        df['distance'] = df.apply(lambda x: int(haversine((curr_latitude, curr_longitude),(float(x['latitude']), float(x['longitude'])), unit='m')),axis=1 ) 
        df['distance'] = df['distance'].apply(lambda x: float(round((x)/1000,1)))
        
        
        # # 주변거리 기준 필터링(15km 이내) 거리 필터는 우선 꺼두자
        # df = df[df['distance']<150]
        df = df.sort_values(by='distance')
        
        # 맛집명 검색기능 ======================== ======================== ========================
        if name != "default":
            df = df[df['name'].str.contains(name)]
        
        # 맛집명 검색결과가 없다면?
        if len(df)==0:
            return render(request,'nyam/empty_feed.html',context=dict(mainfeeds=df),status=200) #context html로 넘길것
            
        
        # 태그명 검색기능 ========================= ======================== ========================
        if tag != "default":     
            # tag cond
            df = df[df['vectors'].str.contains(tag)]
        # 태그 검색결과가 없다면?
        if len(df)==0:
            return render(request,'nyam/empty_feed.html',context=dict(mainfeeds=df),status=200) #context html로 넘길것
        # =============================.
        

        # 50개 이내로 추출
        df = df.iloc[:20,:]

        # 출력된 맛집 id만 출력
        feed_restaurant_id_list =  df['restaurant_id'].values
        
        # 출력된 맛집 id에 해당하는 유저 피드 데이터만 가져오기
        user_data_list = UserData.objects.filter(restaurant_id__in=feed_restaurant_id_list)
              

        #좋아요 싫어요 초기화
        df['like']=0
        df['hate']=0
        df['bookmark']=0
        
        # 간소화 주소 
        df['road_address_short'] = df['road_address'].apply(lambda x: " ".join(x.split(" ")[:3])) 


        # DB 조회 후, df 내 value 변경
        for restaurant_id in df['restaurant_id'].values:
            # 좋아요 수 가져오기
            like_count = Like.objects.filter(restaurant_id=restaurant_id, is_like=True).count()
            cond = df['restaurant_id']==restaurant_id
            df.loc[cond,'like'] = like_count
            
            # 싫어요 수 가져오기
            hate_count = Hate.objects.filter(restaurant_id=restaurant_id, is_hate=True).count()
            cond = df['restaurant_id']==restaurant_id
            df.loc[cond,'hate'] = hate_count
            
            # 북마크 가져오기
            # restaurant_id 기준 유저 개인의 북마크 기록 가져오기
            bookmark_count = Bookmark.objects.filter(restaurant_id=restaurant_id, is_marked=True).count()
            cond = df['restaurant_id']==restaurant_id
            df.loc[cond,'bookmark'] = bookmark_count


        # 유저로그 분기 =========================================================================
        
        # 유저로그가 없는 경우
        if len(user_data_list)==0:
            
            # 1. img_url 추출
            # 캐러셀로 구현을 위해 이미지 리스트를 넘겨줌
            df['img_url'] =  df['img_url'].apply(lambda x: literal_eval(x)) 
            
            # 2. 맛집명이 공백이 있을경우, 캐러셀 작동 오류가 있으므로 맛집명의 공백을 _로 변경함
            df['name'] =  df['name'].apply(lambda x: x.replace(" ","_"))
            
            # 3. vector 전처리
            df['vectors_1row'] =  df['vectors'].apply(lambda x: literal_eval(x)[:5])
            df['vectors_2row'] =  df['vectors'].apply(lambda x: literal_eval(x)[5:10])
            

        # 유저 로그가 있는 경우
        else:            
            # 필터링 된 유저로그를 데이터프레임으로 변환
            user_df =  pd.DataFrame(list(user_data_list.values())).reset_index(drop=True)
            user_id_list = [re.sub(r"\s",'',user_id) for user_id in user_data_list.values_list("user_id",flat=True)]
            
            
            # 유저 점수 정보 가져오기
            user_info = User.objects.filter(nickname__in=user_id_list)
            user_info = pd.DataFrame(list(user_info.values()))
            user_info = user_info[['nickname','email','point']]
            user_info.columns = ['user_id','email', 'point']
            
            # 활성유저 리스트 추출
            # 현재 active 상태인지 확인후, active 상태의 유저만 추출
            valid_user_list = User.objects.filter(is_active="active").values_list("nickname",flat=True)

            
            # 데이터 전처리
            user_df['user_id'] = user_df['user_id'].apply(lambda x : re.sub(r"\s",'',x))
            
            # 활성유저 피드데이터만 필터링
            cond = user_df['user_id'].isin(valid_user_list) 
            #메모리 간소화
            del valid_user_list
            user_df = user_df[cond]
            
            
            # 유저 점수테이블과 결합
            user_df = pd.merge(user_df,user_info, how='left', on='user_id')
            # 높은 점수순의 아이디 출력 (이미지 우선)
            user_df = user_df.sort_values(by='point', ascending=False)
            
            
            # 작성자 리스트 초기화
            df['writers'] = "[]"
            
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
                #메모리 간소화
                del new_img_list
                # vector 변경
                user_comment = user_df.loc[idx_user_df,'comment']
                
                new_comment =  df.loc[cond,'comment'].values[0] +" " + user_comment
                new_vectors = list(toVector(new_comment)[0])
                df.loc[cond,'vectors'] = str(new_vectors)
                #메모리 간소화
                del new_comment
                del new_vectors
                
                # 작성자 이름 반영                
                writer_list = list(user_df[user_df['name']==name]['user_id'].values)
                df.loc[cond,'writers'] = str(writer_list)
                #TODO writers의 point순으로 정렬할 것

            # 딕셔너리 점수 반영 로직

            
            
            # 현재 위치 저장
            df['curr_place'] = str(latitude) +"," + str(longitude)
  
            # 1. img_url 추출
            # 캐러셀로 구현을 위해 이미지 리스트를 넘겨줌
            df['img_url'] =  df['img_url'].apply(lambda x: " ".join(literal_eval(str(x))).split(" "))
            
            
            # 2. writers 추출
            # writers 리스트를 넘겨줌
            df['writers'] =  df['writers'].apply(lambda x: list(set(literal_eval(x))))
            
            # 3. 맛집명이 공백이 있을경우, 캐러셀 작동 오류가 있으므로 맛집명의 공백을 _로 변경함
            df['name'] =  df['name'].apply(lambda x: x.replace(" ","_"))
            # 4. vector 전처리
            df['vectors_1row'] =  df['vectors'].apply(lambda x: literal_eval(x)[:5])
            df['vectors_2row'] =  df['vectors'].apply(lambda x: literal_eval(x)[5:10]) 

        # 결과물 출력
        df = df.to_dict('records')
        
            
        # 결과 df 유효성 확인
        if len(df)<1:
             return render(request,'nyam/empty_feed.html',context=dict(mainfeeds=df, search_keyword=search_keyword),status=200) #context html로 넘길것        
        
        # # 세션정보가 있는 상태에서만 main 창을 보여줄것
        return render(request,'nyam/main_feed_guest.html',context=dict(mainfeeds=df,search_keyword=search_keyword),status=200) #context html로 넘길것
        
    
    
class Main(APIView):
    def get(self, request): 
        # DB 내 queryset 호출 

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
        return render(request,"nyam/main.html", context=dict( user=user)) #context html로 넘길것

    def post(self, request):
        return render(request,"nyam/main.html")
    
    
class MainFeed(APIView):
    def get(self, request): 
        # 쿼리 받아오기
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        tag = request.GET.get('tag')
        address = request.GET.get('address')
        name = request.GET.get('name')
        error= request.GET.get('error')
        
        # 검색어 체크
        search_keyword = ""
        if address!= "default":
            search_keyword = address
        if tag!= "default":
            search_keyword = tag
        if name!= "default":
            search_keyword = name

        
        # 검색어 적정성 확인 error는 error, correct로 나뉨
        if error =="error":
             return render(request,'nyam/search_guide.html',status=200) #context html로 넘길것
         
        # 세션 받아오기
        email = request.session.get('email', None)
        
                            
        # 세션정보가 없는경우
        if email is None:
            return render(request,"user/login.html") #login html로 넘길것
        
        # # 세션 정보가 입력된 경우 데이터 가져오기       
        user = User.objects.filter(email=email).first()
        
        # # 회원 정보가 다르다면?
        if user is None:
            return render(request,"user/login.html") #context html로 넘길것 
        
        
        # 데이터 조회 시작
        
        # 주소 검색기능  ======================== ======================== ========================
        # 만약 주소값이 입력이 됐다면,
        if address!="default":
            curr_location = getLocationFromAddress(address,latitude, longitude)
            curr_latitude = float(curr_location['latitude'])
            curr_longitude = float(curr_location['longitude'])
            result = curr_location['result']
            
        # 만약 주소값이 입력되지 않았다면(= default)
        else:
            curr_latitude = float(latitude)
            curr_longitude = float(longitude)
            result = "sucess"
        
        # DB 내 모든 queryset 호출 
        feed_list = Feed.objects.all()  #select * from content_feed;
        
        
        #데이터프레임으로 변환
        df =  pd.DataFrame(list(feed_list.values()))
        
        #메모리 간소화
        del feed_list
        
        # 한국 데이터 필터링
        cond = ((df['latitude'] >= 32)&(44 >= df['latitude'])) | ((df['longitude']>=123) & (133 >= df['longitude']))
        df = df[cond]
        
        # 현재 위치기준 거리별 정렬 
        df['distance'] = df.apply(lambda x: int(haversine((curr_latitude, curr_longitude),(float(x['latitude']), float(x['longitude'])), unit='m')),axis=1 ) 
        df['distance'] = df['distance'].apply(lambda x: float(round((x)/1000,1)))
        
        # # 주변거리 기준 필터링(15km 이내) 거리 필터는 우선 꺼두자
        # df = df[df['distance']<150]
        df = df.sort_values(by='distance')
        
        
        # 맛집명 검색기능 ======================== ======================== ========================
        if name != "default":
            df = df[df['name'].str.contains(name)]
        
        # 맛집명 검색결과가 없다면?
        if len(df)==0:
            return render(request,'nyam/empty_feed.html',context=dict(mainfeeds=df),status=200) #context html로 넘길것
            
        
        # 태그명 검색기능 ========================= ======================== ========================
        if tag != "default":     
            # tag cond
            df = df[df['vectors'].str.contains(tag)]
            
        # 태그 검색결과가 없다면?
        if len(df)==0:
            return render(request,'nyam/empty_feed.html',context=dict(mainfeeds=df),status=200) #context html로 넘길것
        # =============================.

        # 50개 이내로 추출
        df = df.iloc[:20,:]

        # 출력된 맛집 id만 출력
        feed_restaurant_id_list =  df['restaurant_id'].values
        
        # 출력된 맛집 id에 해당하는 유저 피드 데이터만 가져오기
        user_data_list = UserData.objects.filter(restaurant_id__in=feed_restaurant_id_list)

        #좋아요 싫어요 초기화
        df['like']=0
        df['hate']=0
        df['bookmark']=0
        df['is_like']=False
        df['is_hate']=False
        df['is_marked']=False
        
        # 간소화 주소 
        df['road_address_short'] = df['road_address'].apply(lambda x: " ".join(x.split(" ")[:3])) 

        # DB 조회 후, df 내 value 변경
        for restaurant_id in df['restaurant_id'].values:
            # 좋아요 수 가져오기
            like_count = Like.objects.filter(restaurant_id=restaurant_id, is_like=True).count()
            # restaurant_id 기준 유저 개인의 좋아요 기록 가져오기
            is_like = Like.objects.filter(restaurant_id=restaurant_id, email=email ,is_like=True).exists()
            cond = df['restaurant_id']==restaurant_id
            df.loc[cond,'like'] = like_count
            df.loc[cond,'is_like'] = is_like
            
            # 싫어요 수 가져오기
            hate_count = Hate.objects.filter(restaurant_id=restaurant_id, is_hate=True).count()
            # restaurant_id 기준 유저 개인의 싫어요 기록 가져오기
            is_hate = Hate.objects.filter(restaurant_id=restaurant_id, email=email ,is_hate=True).exists()
            df.loc[cond,'hate'] = hate_count
            df.loc[cond,'is_hate'] = is_hate
            
            # 북마크 가져오기
            # restaurant_id 기준 유저 개인의 북마크 기록 가져오기
            bookmark_count = Bookmark.objects.filter(restaurant_id=restaurant_id, is_marked=True).count()
            is_marked = Bookmark.objects.filter(restaurant_id=restaurant_id, email=email ,is_marked=True).exists()
            df.loc[cond,'bookmark'] = bookmark_count
            df.loc[cond,'is_marked'] = is_marked
            

        # 유저로그 분기 =========================================================================
        
        # 유저로그가 없는 경우
        if len(user_data_list)==0:
            
            # 1. img_url 추출
            # 캐러셀로 구현을 위해 이미지 리스트를 넘겨줌
            df['img_url'] =  df['img_url'].apply(lambda x: literal_eval(x)) 
            
            # 2. 맛집명이 공백이 있을경우, 캐러셀 작동 오류가 있으므로 맛집명의 공백을 _로 변경함
            df['name'] =  df['name'].apply(lambda x: x.replace(" ","_"))
            
            # 3. vector 전처리
            df['vectors_1row'] =  df['vectors'].apply(lambda x: literal_eval(x)[:5])
            df['vectors_2row'] =  df['vectors'].apply(lambda x: literal_eval(x)[5:10])

        # 유저 로그가 있는 경우
        else:            
            # 필터링 된 유저로그를 데이터프레임으로 변환
            user_df =  pd.DataFrame(list(user_data_list.values())).reset_index(drop=True)
            user_id_list = [re.sub(r"\s",'',user_id) for user_id in user_data_list.values_list("user_id",flat=True)]
      
            # 유저 점수 정보 가져오기
            user_info = User.objects.filter(nickname__in=user_id_list)
            user_info = pd.DataFrame(list(user_info.values()))
            user_info = user_info[['nickname','email','point']]
            user_info.columns = ['user_id','email', 'point']
            
            # 활성유저 리스트 추출
            # 현재 active 상태인지 확인후, active 상태의 유저만 추출
            valid_user_list = User.objects.filter(is_active="active").values_list("nickname",flat=True)

            # 데이터 전처리
            user_df['user_id'] = user_df['user_id'].apply(lambda x : re.sub(r"\s",'',x))
             
            # 활성유저 피드데이터만 필터링
            cond = user_df['user_id'].isin(valid_user_list) 
            #메모리 간소화
            del valid_user_list
            user_df = user_df[cond]
            
            
            # 유저 점수테이블과 결합
            user_df = pd.merge(user_df,user_info, how='left', on='user_id')
            # 높은 점수순의 아이디 출력 (이미지 우선)
            user_df = user_df.sort_values(by='point', ascending=False)
            
            
            # 작성자 리스트 초기화
            df['writers'] = "[]"
            
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
                #메모리 간소화
                del new_img_list
                # vector 변경
                user_comment = user_df.loc[idx_user_df,'comment']
                
                new_comment =  df.loc[cond,'comment'].values[0] +" " + user_comment
                new_vectors = list(toVector(new_comment)[0])
                df.loc[cond,'vectors'] = str(new_vectors)
                #메모리 간소화
                del new_comment
                del new_vectors
                
                # 작성자 이름 반영                
                writer_list = list(user_df[user_df['name']==name]['user_id'].values)
                df.loc[cond,'writers'] = str(writer_list)
                #TODO writers의 point순으로 정렬할 것

            # 딕셔너리 점수 반영 로직
            
            
            
            # 현재 위치 저장
            df['curr_place'] = str(latitude) +"," + str(longitude)
  
            # 1. img_url 추출
            # 캐러셀로 구현을 위해 이미지 리스트를 넘겨줌
            df['img_url'] =  df['img_url'].apply(lambda x: " ".join(literal_eval(str(x))).split(" "))
            
            
            # 2. writers 추출
            # writers 리스트를 넘겨줌
            
            df['writers'] =  df['writers'].apply(lambda x: list(set(literal_eval(x))))
            
            # 3. 맛집명이 공백이 있을경우, 캐러셀 작동 오류가 있으므로 맛집명의 공백을 _로 변경함
            df['name'] =  df['name'].apply(lambda x: x.replace(" ","_"))
            # 4. vector 전처리
            df['vectors_1row'] =  df['vectors'].apply(lambda x: literal_eval(x)[:5])
            df['vectors_2row'] =  df['vectors'].apply(lambda x: literal_eval(x)[5:10]) 

        # 결과물 출력
        df = df.to_dict('records')
        
        # 결과 df 유효성 확인
        if len(df)<1:
             return render(request,'nyam/empty_feed.html',context=dict(mainfeeds=df, search_keyword=search_keyword),status=200) #context html로 넘길것        
        
        # # 세션정보가 있는 상태에서만 main 창을 보여줄것
        return render(request,'nyam/main_feed.html',context=dict(mainfeeds=df,search_keyword=search_keyword),status=200) #context html로 넘길것
        
        
    
    