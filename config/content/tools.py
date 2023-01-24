from konlpy.tag import Okt
from collections import Counter

import re
from geopy.geocoders import Nominatim
geo_local = Nominatim(user_agent='South Korea')

def getLocationFromAddress(address):
    geo = geo_local.geocode(address)
    crd = {"latitude": geo.latitude, "longitude": geo.longitude}
    return crd






okt = Okt()

def toVector(phrase, minmum_frequency=2, length_conditions=2):
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
    new_phrase = re.sub(r",", "", new_phrase)
    # 명사만 추출
    noun_list = okt.nouns(new_phrase)
    # 명사 빈도수 
    noun_list_count = Counter(noun_list)

    # 빈도순 정렬
    main_noun_list_count = noun_list_count.most_common(200)
    # 길이가 2자 이상인 명사, 빈도수가 3회 이상인 단어만
    main_noun_list_count = [n[0] for n in main_noun_list_count if (len(n[0])>length_conditions) and (n[1]>=minmum_frequency)][:50]
    
    # # 명사 빈도수 딕셔너리 
    noun_dict_count = dict(noun_list_count)
    return [main_noun_list_count,noun_dict_count]
