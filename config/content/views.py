#REST 호출이 가능하도록 설정
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from content.models import Feed, UserData
from uuid import uuid4
import pandas as pd
import random
from ast import literal_eval
import os
from config.settings import MEDIA_ROOT


import re
from geopy.geocoders import Nominatim
geo_local = Nominatim(user_agent='South Korea')


from ast import literal_eval
from konlpy.tag import Hannanum
from collections import Counter
han = Hannanum()

#TODO 이건 나중에 다른곳으로 옮겨야함!
def getLocationFromAddress(address):
    geo = geo_local.geocode(address)
    crd = {"latitude": geo.latitude, "longitude": geo.longitude}
    return crd

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
    main_noun_list_count = noun_list_count.most_common(200)
    # 길이가 2자 이상인 명사, 빈도수가 3회 이상인 단어만
    main_noun_list_count = [n[0] for n in main_noun_list_count if (len(n[0])>length_conditions) and (n[1]>=minmum_frequency)][:50]
    return main_noun_list_count

    
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
        
        #TODO 데이터 적합성 테스트 (주소 유효성 확인(완료), 이미지가 음식사진인지 테스트, 불건전한 문구 또는 텍스트가 있는경우 제외 알고리즘)  모든 조건이 양호한경우에 1차 유저정보에 반영 
        
        # 1. image 적합성 테스트(음식 이미지 확인 관련 코드) 
        
        # 2. 주소 유효성 테스트
        crd = getLocationFromAddress(road_address)
        # 대한민국 경도/ 위도 범위  동경 124°∼132°, 북위 33°∼43°        
        if (crd['latitude'] <= 32)or(44 <= crd['latitude']) or (crd['longitude']<=123) or (133 <= crd['longitude']):
            return Response(status=400)
        # 3. 전화번호 적합성 테스트
        if len((phone_number).split("-"))<3:
            return Response(status=400)
        # 4. 주소 유효성 테스트
 
        # [동일 데이터 유무확인] 값이 있다면 기존값을 가져올것 맛집명과 전화번호가 같은경우로 인식
        db_test =  Feed.objects.filter(name=name, phone_number=phone_number)
        
        # 기존에 파일이 있는 경우
        # id 유지, 식당명 유지, 주소 유지, 전화번호 유지, 위도/경도 유지, 평점 유지, img_url리스트를 가져와 리스트 추가 후 입력, restaurant_type 미입력, like/hate 유지  comment 추가 및 vector 재생성
        if (len(db_test)>=1):

            # 해당 DB data를 가져온다.
            db_data = Feed.objects.get(name=name, phone_number=phone_number)
            # 이미지 리스트를 가져와 신규 이미지를 추가한다. (literal_eval().append 오류)
            img_list = " ".join(literal_eval(db_data.img_url))
            img_list +=f" {image}"
            img_list = img_list.split(" ")
            db_data.img_url = img_list
            # comment를 추가한다.
            db_data.comment = db_data.comment +" " + comment
            # 새롭게 추가된 comment의 vector를 구한다.
            db_data.vectors = toVector(db_data.comment)
            # 수정된 값을 저장한다.
            db_data.save()
            
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
            new_vectors = toVector(comment)
            
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
                like=like,
                hate=hate
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
