import pandas as pd
import re
from konlpy.tag import Twitter
from collections import Counter
from tqdm import tqdm

tqdm.pandas()

han = Twitter()
data = pd.read_csv('all_restraunt_data.csv')

# def toVector(phrase, minmum_frequency=2, length_conditions=1):
#     """
#         빈도순으로 50개의 명사를 추출하는 함수
#     """
#     # 한글만 남기기
#     new_phrase = re.sub(r"^[가-힣]", "", phrase)
#     new_phrase = re.sub("([ㄱ-ㅎㅏ-ㅣ]+)", "", new_phrase)
#     new_phrase = re.sub("([0-9])", "", new_phrase)
#     # 일부 특수문자 제거
#     new_phrase = re.sub(r"/.", "", new_phrase)
#     # new_phrase = re.sub(r",", "", new_phrase)
#     new_phrase = re.sub(r"_", "", new_phrase)
#     new_phrase = re.sub(r"─", "", new_phrase)
#     # 명사만 추출
#     noun_list = han.nouns(new_phrase)
#     # 명사 빈도수 
#     noun_list_count = Counter(noun_list)

#     # 빈도순 정렬
#     main_noun_list_count = noun_list_count.most_common(200)
#     # 길이가 2자 이상인 명사, 빈도수가 3회 이상인 단어만
#     main_noun_list_count = [n[0] for n in main_noun_list_count if (len(n[0])>length_conditions) and (n[1]>=minmum_frequency)][:50]
    
#     # 명사 빈도수 딕셔너리 
#     noun_dict_count = dict(noun_list_count)
#     return [main_noun_list_count,noun_dict_count]

# data['vectors'] = data['comment'].progress_apply(lambda x: toVector(x)[0])

# data['vectors_dict'] = data['comment'].progress_apply(lambda x: toVector(x)[1])



data= data[['restaurant_id', 'name', 'road_address', 'phone_number', 'latitude', 'longitude',
       'rating', 'img_url', 'comment', 'restaurant_type', 'like',
       'hate','vectors_dict','vectors']]

data.to_csv('all_restraunt_data.csv',index=False)

