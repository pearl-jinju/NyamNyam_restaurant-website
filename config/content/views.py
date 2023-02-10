#REST 호출이 가능하도록 설정
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from content.models import Feed, UserData, Reply, Like, Hate, Bookmark
from django.http import HttpResponseBadRequest, JsonResponse
from user.models import User
from uuid import uuid4
import pandas as pd
import random
from ast import literal_eval
import os
from config.settings import MEDIA_ROOT, SECRET_API_KEY
import string
import re
from konlpy.tag import Okt
from collections import Counter
import googlemaps

# # API키 입력
mykey = SECRET_API_KEY
maps = googlemaps.Client(key=mykey)  # my key값 입력


# 주소 불러오는 함수
from geopy.geocoders import Nominatim
geo_local = Nominatim(user_agent='South Korea')


konlp = Okt()

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

def getLocationFromAddress(address):
    try:
        geo = geo_local.geocode(address)
        crd = {"latitude": geo.latitude, "longitude": geo.longitude}
    except:
        return None
    return crd


def getLocationFromAddress(address):
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
        return None
        
    curr_location = {"latitude": geo_location['location']['lat'], "longitude":  geo_location['location']['lng'], "result":"success"}
    return curr_location


    
class UploadFeed(APIView):
    def post(self, request):
        
        # html ajax을 통해 python으로 Data를 받음
        # 파일을 불러오는 코드
        file = request.FILES['file']
        uuid_name =uuid4().hex
        save_path = os.path.join(MEDIA_ROOT, uuid_name)
        
        # 파일을 저장하는 코드
        with open(save_path,"wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        image = uuid_name
        user_id = request.data.get('user_id')
        name = request.data.get('name')
        road_address = request.data.get('road_address')
        phone_number = request.data.get('phone_number')
        comment = request.data.get('comment')
        like = 0
        hate = 0
        
        if name=="":
            return JsonResponse({"error": "맛집명을 입력하세요."}, status=400)
        if road_address=="":
            return JsonResponse({"error": "주소를 입력하세요."}, status=400)
        if phone_number=="":
            return JsonResponse({"error": "전화번호를 입력하세요."}, status=400)
        if comment=="":
            return JsonResponse({"error": "한줄평을 입력하세요."}, status=400)
        
        #TODO 데이터 적합성 테스트 (주소 유효성 확인(완료), 이미지가 음식사진인지 테스트, 불건전한 문구 또는 텍스트가 있는경우 제외 알고리즘)  모든 조건이 양호한경우에 1차 유저정보에 반영 
        
        # 1. image 적합성 테스트(음식 이미지 확인 관련 코드) 
        
        # 2. 주소 유효성 테스트(임시)
        crd = getLocationFromAddress(road_address)

        if crd is None:
            return JsonResponse({"error": "현재 위도 경도를 확인할 수 없습니다."}, status=400)
            
        # 대한민국 경도/ 위도 범위  동경 124°∼132°, 북위 33°∼43°  
        if (crd['latitude'] <= 32)or(44 <= crd['latitude']) or (crd['longitude']<=123) or (133 <= crd['longitude']):
            return JsonResponse({"error": "주소가 올바르지 않습니다."}, status=400)
        
        
        # 3. 전화번호 적합성 테스트        
        if len((phone_number).split("-"))<3:
            return JsonResponse({"error": "전화번호 양식이 올바르지 않습니다 '-'를 포함해주세요. "}, status=400)
        
        # 4. name 검증 및 내 특수문자 제거
        name = name.translate(str.maketrans('', '', string.punctuation))

 
        # [동일 데이터 유무확인] 값이 있다면 기존값을 가져올것 맛집명과 주소가 같은경우로 인식
        db_test =  Feed.objects.filter(name=name, phone_number=phone_number)
        
        # 기존에 파일이 있는 경우
        # id 유지, 식당명 유지, 주소 유지, 전화번호 유지, 위도/경도 유지, 평점 유지, img_url리스트를 가져와 리스트 추가 후 입력, restaurant_type 미입력, like/hate 유지  comment 추가 및 vector 재생성
        if (len(db_test)>=1):

            # 해당 DB data를 가져온다.
            db_data = Feed.objects.get(name=name, phone_number=phone_number)
            
            # 기존 DB에서 유저 DB입력정보 가져오기
            # 맛집의 id를 가져온다
            restaurant_id =  db_data.restaurant_id
            restaurant_type = "-"
            
            # 유저 DB에 입력하기
            UserData.objects.create(
                restaurant_id = restaurant_id,
                user_id=user_id,
                name=name,
                road_address=road_address,
                phone_number=phone_number,
                img_url=[image],
                comment=comment,
                restaurant_type=restaurant_type,
                )
            return Response(status=200)
            
        # 기존에 파일이 없는 경우(신규 등록)
        # 가장최근 id 가져온후 +1 부여, 식당명 입력, 주소 입력, 전화번호 입력, 위도/경도 계산값 입력, 평점 0값 입력, img_url리스트를 가져와 리스트 추가 후 입력, restaurant_type 미입력, like/hate 0으로 입력
        else:
            # 가장 최근의 id 값을 가져옴
            last_id = Feed.objects.last().restaurant_id
            new_id = int(last_id) + 1
            # 식당명 입력
            new_name = name
            # 주소 입력
            new_road_address = road_address

                
            latitude = crd['latitude']
            longitude = crd['longitude']
            
            # 전화번호 입력
            new_phone_number = phone_number
            # 평점 초기화 
            rating = 0
            # 이미지 주소 입력
            img_url_list = str([image])
            # restaurant_type 미입력
            restaurant_type = "-"
            #comment 초기화
            new_comment = comment
            
            
            #vector 추출
            vector_result = toVector(comment)
            #vector_list 추출
            new_vectors = vector_result[0]
            #vector_dict 추출
            new_vectors_dict = vector_result[1]
            
            # user tag act log 가져오기
            
            #like/hate 초기화
            like = 0
            hate = 0

            Feed.objects.create(
                restaurant_id = new_id,
                name=new_name,
                road_address=new_road_address,
                phone_number=new_phone_number,
                latitude=latitude,
                longitude=longitude,
                rating=rating,
                img_url=img_url_list,
                comment=new_comment,
                restaurant_type=restaurant_type,
                vectors=new_vectors,
                vectors_dict = new_vectors_dict,
                like=like,
                hate=hate,
                # vectors_dict=
                )
            # 유저 DB에 입력하기
            UserData.objects.create(
                restaurant_id = new_id,
                user_id=user_id,
                name=new_name,
                road_address=new_road_address,
                phone_number=new_phone_number,
                img_url=img_url_list,
                comment=new_comment,
                restaurant_type=restaurant_type,
                )
        
            return Response(status=200)

class DeleteFeed(APIView):
    def delete(self, request):
        feed_id = request.data.get('feed_id')

        email = request.session.get('email', None)
        
        # 비정상 접근 체크
        if email is None:
            return JsonResponse({"error": "비정상적 접근입니다."}, status=400)
        
        # 현재 session의 이메일에 해당하는 유저 닉네임 확인

        # 삭제 대상 feed data확인
        delete_target_data = UserData.objects.filter(user_data_seq=feed_id).first()
        
        # 만약 현재유저 닉네임 매치되는게 없다면?
        if not delete_target_data:
            return JsonResponse({"error": "비정상적 접근입니다."}, status=400)
        
        delete_target_data.delete()

        return Response(status=200)
        
class EditFeed(APIView):
    def put(self, request):
        email = request.session.get('email', None)
        
        # 비정상 접근 체크
        if email is None:
            return JsonResponse({"error": "비정상적 접근입니다."}, status=400)
        # PUT 데이터의 유형구분
        edit_type = request.data['edit_type']

        
        # 기존 이미지 업로드 라면
        if edit_type=="original":
            # user_data_seq으로 데이터 탐색
            user_data_seq = request.data['feed_id']
            edit_target_data = UserData.objects.filter(user_data_seq=user_data_seq).first()
            # 새로운 입력값 받아오기
            user_id = request.data['user_id']
            name = request.data['name']
            road_address = request.data['road_address']
            phone_number = request.data['phone_number']
            comment = request.data['comment']
            
            
            edit_target_data.name = name
            edit_target_data.road_address = road_address
            edit_target_data.phone_number = phone_number
            edit_target_data.comment = comment
            edit_target_data.save()
            
            
        else:
            # user_data_seq으로 데이터 탐색
            user_data_seq = request.data['feed_id']
            edit_target_data = UserData.objects.filter(user_data_seq=user_data_seq).first()
            # 새로운 입력값 받아오기
            user_id = request.data['user_id']
            name = request.data['name']
            road_address = request.data['road_address']
            phone_number = request.data['phone_number']
            comment = request.data['comment']
            
            file = request.data['file']
            
            uuid_name =uuid4().hex
            save_path = os.path.join(MEDIA_ROOT, uuid_name)
            # 파일을 저장하는 코드
            with open(save_path,"wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            # 변수명 및 양식 통일 
            image = [uuid_name]
        
            edit_target_data = UserData.objects.filter(user_id=user_id, comment=comment).first()
            # 데이터 수정
            edit_target_data.name = name
            edit_target_data.img_url = image
            edit_target_data.road_address = road_address
            edit_target_data.phone_number = phone_number
            edit_target_data.comment = comment
            edit_target_data.save()
        
        return Response(status=200)
        
        
        
    def get(self, request):
        feed_id = request.GET.get('feed_id')
        
        email = request.session.get('email', None)
        
        # 비정상 접근 체크
        if email is None:
            return JsonResponse({"error": "비정상적 접근입니다."}, status=400)
        
        edit_target_data = UserData.objects.filter(user_data_seq=feed_id).first()
        name = edit_target_data.name
        road_address = edit_target_data.road_address
        phone_number = edit_target_data.phone_number
        img_url = literal_eval(edit_target_data.img_url)[0]
        comment = edit_target_data.comment
        
        data={
            "name":name,
            "road_address":road_address,
            "phone_number":phone_number,
            "img_url":img_url,
            "comment":comment
        }
        
        return Response(status=200, data=data)
        

        # feed_id = request.data.get('feed_id')
        
        # email = request.session.get('email', None)
        
        # # 비정상 접근 체크
        # if email is None:
        #     return JsonResponse({"error": "비정상적 접근입니다."}, status=400)
        
        # edit_target_data = UserData.objects.filter(user_data_seq=feed_id).first()
        # name = edit_target_data.name
        # road_address = edit_target_data.road_address
        # phone_number = edit_target_data.phone_number
        # img_url = edit_target_data.img_url[0]
        # comment = edit_target_data.comment
        
        # data={
        #     "name":name,
        #     "road_address":road_address,
        #     "phone_number":phone_number,
        #     "img_url":img_url,
        #     "comment":comment
        # }
        
        # return Response(status=200, data=data)
 
        

class Profile(APIView):
    """_    내 프로필을 볼때
    Args:
        APIView (_type_): _description_
    """
    def get(self, request):
        # 세션 정보 받아오기
        #  로그인 관련 정보 출력
        email = request.session.get('email', None)
        
        # 내 프로필에 접근하는 경우인지 확인해야함
        # 세션정보가 없는경우
        if email is None:
             return render(request,"user/login.html") #context html로 넘길것
        
        # # 세션 정보가 입력된 경우 데이터 가져오기       
        user = User.objects.filter(email=email).first()
        
        # # 회원 정보가 다르다면?
        if user is None:
            return render(request,"user/login.html") #context html로 넘길것 
        

        # 사용자 ID 기준으로 작성 및 업로드한 피드 리스트 호출 (최종형태 df)
        user_data =  UserData.objects.all()
         
        feed_list =  pd.DataFrame(list(user_data.values())).reset_index(drop=True)
        # user_id filter 적용이 안됨.. df 변환 및 데이터 전처리 후 df 필터링
        feed_list['user_id'] = feed_list['user_id'].apply(lambda x : re.sub(r"\r",'',x))
        feed_list['user_id'] = feed_list['user_id'].apply(lambda x : re.sub(r"\n",'',x))
        feed_list['user_id'] = feed_list['user_id'].apply(lambda x : re.sub(" ",'',x))
        feed_list['user_id'] = feed_list['user_id'].apply(lambda x : str(x))
        
        cond = feed_list['user_id']==user.nickname
        feed_list = feed_list[cond]
        
        # 결과 피드 리스트가 있다면,
        if len(feed_list['restaurant_id'].values)>0:
            
            feed_list_restaurant_ids= feed_list['restaurant_id'].values
        
            for feed_list_restaurant_id in feed_list_restaurant_ids:
                like_count = Like.objects.filter(restaurant_id=feed_list_restaurant_id).count()
                hate_count = Hate.objects.filter(restaurant_id=feed_list_restaurant_id).count()
                bookmark_count = Bookmark.objects.filter(restaurant_id=feed_list_restaurant_id).count()
                cond = feed_list['restaurant_id']==feed_list_restaurant_id
                feed_list.loc[cond,'like_count'] = like_count
                feed_list.loc[cond,'hate_count'] = hate_count
                feed_list.loc[cond,'bookmark_count'] = bookmark_count
        else:
            # 없다면, 0으로
            feed_list['like_count'] = 0
            feed_list['hate_count'] = 0
            feed_list['bookmark_count'] = 0
        
                
        # 왜 값을 넣을 때  int()가 안먹히는 걸까
        feed_list['like_count'] = feed_list['like_count'].apply(lambda x: int(x))
        like_sum = feed_list['like_count'].sum()
        feed_list['hate_count'] = feed_list['hate_count'].apply(lambda x: int(x))
        hate_sum = feed_list['hate_count'].sum()
        feed_list['bookmark_count'] = feed_list['bookmark_count'].apply(lambda x: int(x))
        bookmark_sum = feed_list['bookmark_count'].sum()

        # 결과 피드가 있다면
        if len(feed_list)>0:
            # 이미지 리스트형식을 문자열로 변경
            feed_list['img_url'] =  feed_list['img_url'].apply(lambda x: literal_eval(str(x))[0])
            feed_list = feed_list.loc[::-1]
            feed_list = feed_list.to_dict('records')
            
            feed_count = len(feed_list)
        else:
            feed_list = "empty"
            feed_count = 0
            

        
        #(최종형태 Queryset)
         
        # 좋아요 목록
        like_list = list(Like.objects.filter(email=email, is_like=True).values_list('restaurant_id', flat=True))  #쿼리셋을 리스트로 만드는 방법
        
        # 좋아요 기록이 있다면
        if len(like_list)>0:
                
            like_feed_list = Feed.objects.filter(restaurant_id__in=like_list)
            
            like_feed_list =  pd.DataFrame(list(like_feed_list.values())).reset_index(drop=True)
            # 이미지 리스트형식을 문자열로 변경
            like_feed_list['img_url'] =  like_feed_list['img_url'].apply(lambda x: literal_eval(str(x))[0])
            like_feed_list = like_feed_list.loc[::-1]
            like_feed_list = like_feed_list.to_dict('records')
            
        # 없다면
        else:
            like_feed_list="empty"
        
        
        
        # 싫어요 목록
        hate_list = list(Hate.objects.filter(email=email, is_hate=True).values_list('restaurant_id', flat=True))  #쿼리셋을 리스트로 만드는 방법
        # 싫어요 기록이 있다면
        if len(hate_list)>0:
            hate_feed_list = Feed.objects.filter(restaurant_id__in=hate_list)
                    
            hate_feed_list =  pd.DataFrame(list(hate_feed_list.values())).reset_index(drop=True)
            # 이미지 리스트형식을 문자열로 변경
            hate_feed_list['img_url'] =  hate_feed_list['img_url'].apply(lambda x: literal_eval(str(x))[0])
            hate_feed_list = hate_feed_list.loc[::-1]
            hate_feed_list = hate_feed_list.to_dict('records')
            
        # 없다면
        else:
            hate_feed_list="empty"
        
        
        # 북마크 목록
        bookmark_list = list(Bookmark.objects.filter(email=email, is_marked=True).values_list('restaurant_id', flat=True))  #쿼리셋을 리스트로 만드는 방법
        # 북마크 기록이 있다면
        if len(bookmark_list)>0:    
            bookmark_feed_list = Feed.objects.filter(restaurant_id__in=bookmark_list)
            bookmark_feed_list =  pd.DataFrame(list(bookmark_feed_list.values())).reset_index(drop=True)
            # 이미지 리스트형식을 문자열로 변경
            bookmark_feed_list['img_url'] =  bookmark_feed_list['img_url'].apply(lambda x: literal_eval(str(x))[0])
            bookmark_feed_list = bookmark_feed_list.loc[::-1]
            bookmark_feed_list = bookmark_feed_list.to_dict('records')
            
        # 없다면
        else:
            bookmark_feed_list='empty'
            
        return render(request, "content/profile.html", context=dict(feed_list=feed_list,
                                                                    like_feed_list=like_feed_list,
                                                                    hate_feed_list=hate_feed_list,
                                                                    bookmark_feed_list=bookmark_feed_list,                                                                    
                                                                    user=user,
                                                                    feed_count=feed_count,                                                                    
                                                                    like_sum=like_sum,
                                                                    hate_sum=hate_sum,
                                                                    bookmark_sum=bookmark_sum
                                                                    ))
    
#TODO 다른사람의 프로필을 볼수 있도록 설정할것
class UserProfile(APIView):
    """_    다른사람의 프로필을 볼때
    Args:
        APIView (_type_): _description_
    """
    def get(self, request):
        

        
        # 세션 정보 받아오기
        #  로그인 관련 정보 출력
        email = request.session.get('email', None)
                # 내 프로필에 접근하는 경우인지 확인해야함
        # 세션정보가 없는경우
        if email is None:
             return render(request,"user/login.html") #context html로 넘길것
        
        # # 세션 정보가 입력된 경우 데이터 가져오기       
        nowuser = User.objects.filter(email=email).first()
        
        # # 회원 정보가 다르다면?
        if nowuser is None:
            return render(request,"user/login.html") #context html로 넘길것 
        
        # 다른 유저의 ID
        username = request.GET.get('username')
        
        # 쿼리에 입력된 다른유저의 닉네임을 받음      
        username = User.objects.filter(nickname=username).first()
        
        
        # 사용자 ID 기준으로 작성 및 업로드한 피드 리스트 호출 (최종형태 df)
        user_data =  UserData.objects.all()
         
        feed_list =  pd.DataFrame(list(user_data.values())).reset_index(drop=True)
        # user_id filter 적용이 안됨.. df 변환 및 데이터 전처리 후 df 필터링
        feed_list['user_id'] = feed_list['user_id'].apply(lambda x : re.sub(r"\r",'',x))
        feed_list['user_id'] = feed_list['user_id'].apply(lambda x : re.sub(r"\n",'',x))
        feed_list['user_id'] = feed_list['user_id'].apply(lambda x : re.sub(" ",'',x))
        feed_list['user_id'] = feed_list['user_id'].apply(lambda x : str(x))

        
        # 결과 피드 리스트
        feed_list = feed_list[feed_list['user_id']==username.nickname]
        
        feed_list_restaurant_ids = feed_list['restaurant_id'].values
        
        for feed_list_restaurant_id in feed_list_restaurant_ids:
            like_count = Like.objects.filter(restaurant_id=feed_list_restaurant_id).count()
            hate_count = Hate.objects.filter(restaurant_id=feed_list_restaurant_id).count()
            bookmark_count = Bookmark.objects.filter(restaurant_id=feed_list_restaurant_id).count()
            cond = feed_list['restaurant_id']==feed_list_restaurant_id
            feed_list.loc[cond,'like_count'] = like_count
            feed_list.loc[cond,'hate_count'] = hate_count
            feed_list.loc[cond,'bookmark_count'] = bookmark_count
                
        # 왜 값을 넣을 때  int()가 안먹히는 걸까
        feed_list['like_count'] = feed_list['like_count'].apply(lambda x: int(x))
        like_sum = feed_list['like_count'].sum()
        feed_list['hate_count'] = feed_list['hate_count'].apply(lambda x: int(x))
        hate_sum = feed_list['hate_count'].sum()
        feed_list['bookmark_count'] = feed_list['bookmark_count'].apply(lambda x: int(x))
        bookmark_sum = feed_list['bookmark_count'].sum()
        
        
        # 결과 피드가 있다면
        if  len(feed_list)>0:
            # 이미지 리스트형식을 문자열로 변경
            feed_list['img_url'] =  feed_list['img_url'].apply(lambda x: literal_eval(str(x))[0])
            feed_list = feed_list.loc[::-1]
            feed_list = feed_list.to_dict('records')

            feed_count = len(feed_list)
        #없다면
        else:
            feed_list="empty"
            feed_count = 0

        #(최종형태 Queryset)
         
        # 좋아요 목록
        like_list = list(Like.objects.filter(email=username.email, is_like=True).values_list('restaurant_id', flat=True))  #쿼리셋을 리스트로 만드는 방법
        # 좋아요 목록이 있다면
        if  len(like_list)>0:
            like_feed_list = Feed.objects.filter(restaurant_id__in=like_list)
            
            like_feed_list =  pd.DataFrame(list(like_feed_list.values())).reset_index(drop=True)
            # 이미지 리스트형식을 문자열로 변경
            like_feed_list['img_url'] =  like_feed_list['img_url'].apply(lambda x: literal_eval(str(x))[0])
            like_feed_list = like_feed_list.loc[::-1]
            like_feed_list = like_feed_list.to_dict('records')
        # 없다면
        else:
            like_feed_list="empty"

        # 싫어요 목록
        hate_list = list(Hate.objects.filter(email=username.email, is_hate=True).values_list('restaurant_id', flat=True))  #쿼리셋을 리스트로 만드는 방법
        # 싫어요 목록이 있다면
        if len(hate_list)>0:
            hate_feed_list = Feed.objects.filter(restaurant_id__in=hate_list)
                    
            hate_feed_list =  pd.DataFrame(list(hate_feed_list.values())).reset_index(drop=True)
            # 이미지 리스트형식을 문자열로 변경
            hate_feed_list['img_url'] =  hate_feed_list['img_url'].apply(lambda x: literal_eval(str(x))[0])
            hate_feed_list = hate_feed_list.loc[::-1]
            hate_feed_list = hate_feed_list.to_dict('records')
        # 없다면
        else:
            hate_feed_list="empty"
        
        # 북마크 목록
        bookmark_list = list(Bookmark.objects.filter(email=username.email, is_marked=True).values_list('restaurant_id', flat=True))  #쿼리셋을 리스트로 만드는 방법
        # 북마크 기록이 있다면
        if len(bookmark_list)>0:
            bookmark_feed_list = Feed.objects.filter(restaurant_id__in=bookmark_list)
            bookmark_feed_list =  pd.DataFrame(list(bookmark_feed_list.values())).reset_index(drop=True)
            # 이미지 리스트형식을 문자열로 변경
            bookmark_feed_list['img_url'] =  bookmark_feed_list['img_url'].apply(lambda x: literal_eval(str(x))[0])
            bookmark_feed_list = bookmark_feed_list.loc[::-1]
            bookmark_feed_list = bookmark_feed_list.to_dict('records')
        else:
            bookmark_feed_list="empty"
            
        return render(request, "content/userprofile.html", context=dict(feed_list=feed_list,
                                                                    like_feed_list=like_feed_list,
                                                                    hate_feed_list=hate_feed_list,
                                                                    bookmark_feed_list=bookmark_feed_list,                                                                    
                                                                    nowuser=nowuser,
                                                                    otheruser=username,
                                                                    feed_count=feed_count,
                                                                    like_sum=like_sum,
                                                                    hate_sum=hate_sum,
                                                                    bookmark_sum=bookmark_sum
                                                                    ))

class UploadProfile(APIView):
    def post(self, request):
        
        # html ajax을 통해 python으로 Data를 받음
        # 파일을 불러오는 코드
        file = request.FILES['file']
        uuid_name =uuid4().hex
        save_path = os.path.join(MEDIA_ROOT, uuid_name)
        
        # 파일을 저장하는 코드
        with open(save_path,"wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        profile_img = uuid_name
        email = request.data.get('email')
        
        user = User.objects.filter(email=email).first()
        
        user.profile_img = profile_img
        
        user.save()
        
        return Response(status=200)



# class UploadReply(APIView):
#     def post(self, request):
#         feed_id = request.data.get('feed_id', None)
#         reply_content = request.data.get('feed_id', None)
#         email = request.session.get('email', None)
        
#         # 세션정보가 없는경우
#         if email is None:
#              return render(request,"user/login.html") #context html로 넘길것
        
#         # # 세션 정보가 입력된 경우 데이터 가져오기       
#         user = User.objects.filter(email=email).first()
        
#         # # 회원 정보가 다르다면?
#         if user is None:
#             return render(request,"user/login.html") #context html로 넘길것 
        
#         Reply.objects.create(feed_id=feed_id, reply_content=reply_content, email=email)
        
#         return Response(status=200)

class ToggleLike(APIView):
    def post(self, request):
        restaurant_id = request.data.get('restaurant_id', None)
        favorite_text = request.data.get('favorite_text', True)
        
        if favorite_text== "favorite_border":
            is_like = True
        else:
            is_like = False
            
        email = request.session.get('email', None)
        
        
        # 기존 좋아요 여부 확인
        like_exp = Like.objects.filter(restaurant_id=restaurant_id, email=email).first()
        
        # 싫어요 데이터 확인
        hate_exp = Hate.objects.filter(restaurant_id=restaurant_id, email=email, is_hate=1).first()
        
        # 있다면?
        if like_exp:
            like_exp.is_like = is_like
            like_exp.save()
            # 만약 싫어요가 활성화 되어있다면,
            if hate_exp:
                hate_exp.is_hate = False
                hate_exp.save()
            
        # 없다면? 새로저장
        else:    
            Like.objects.create(restaurant_id=restaurant_id, is_like=is_like, email=email)
            # 만약 싫어요가 활성화 되어있다면,
            if hate_exp:
                hate_exp.is_hate = False
                hate_exp.save()
        
        return Response(status=200)
    
class ToggleHate(APIView):
    def post(self, request):
        restaurant_id = request.data.get('restaurant_id', None)
        hate_text = request.data.get('hate_text', True)
        
        if hate_text== "thumb_down_off_alt":
            is_hate = True
        else:
            is_hate = False
            
        email = request.session.get('email', None)
        
        
        # 기존 싫어요 여부 확인
        hate_exp = Hate.objects.filter(restaurant_id=restaurant_id, email=email).first()
        
        # 좋아요 데이터 확인
        like_exp = Like.objects.filter(restaurant_id=restaurant_id, email=email, is_like=1).first()
        
        # 있다면?
        if hate_exp:
            hate_exp.is_hate = is_hate
            hate_exp.save()
            # 만약 좋아요가 활성화 되어있다면,
            if like_exp:
                like_exp.is_like = False
                like_exp.save()
        # 없다면? 새로저장
        else:    
            Hate.objects.create(restaurant_id=restaurant_id, is_hate=is_hate, email=email)
            # 만약 좋아요가 활성화 되어있다면,
            if like_exp:
                like_exp.is_like = False
                like_exp.save()
        
        return Response(status=200)
    
class ToggleBookmark(APIView):
    def post(self, request):
        restaurant_id = request.data.get('restaurant_id', None)
        bookmark_text = request.data.get('bookmark_text', True)
        
        if bookmark_text== "bookmark_border":
            is_marked = True
        else:
            is_marked = False
            
        email = request.session.get('email', None)
        
        
        # 기존 북마크 여부 확인
        bookmark_exp = Bookmark.objects.filter(restaurant_id=restaurant_id, email=email).first()
        
        # 있다면?
        if bookmark_exp:
            bookmark_exp.is_marked = is_marked
            bookmark_exp.save()

        # 없다면? 새로저장
        else:    
            Bookmark.objects.create(restaurant_id=restaurant_id, is_marked=is_marked, email=email)
        
        return Response(status=200)