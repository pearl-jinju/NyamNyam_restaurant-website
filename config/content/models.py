from django.db import models

# Create your models here.
class Feed(models.Model):
    restaurant_id     = models.IntegerField(primary_key=True) # 식당 id 
    name              = models.TextField()   # 맛집 이름
    road_address      = models.TextField()   # 도로명주소
    phone_number      = models.TextField(null="000-0000-0000")   # 전화번호
    latitude          = models.FloatField()  # 위도
    longitude         = models.FloatField()  # 경도
    rating            = models.FloatField()  # 평점
    img_url           = models.TextField()   # img 주소
    comment           = models.TextField(null="-")   # 댓글 모음
    restaurant_type   = models.TextField(null="-")   # 맛집 유형(카페, 음식점)
    vectors           = models.TextField(null="[]")   # 주요 벡터
    vectors_dict      = models.TextField(null="{}")   # 주요 벡터 빈도수
    like              = models.IntegerField(default=0)   # 좋아요
    hate              = models.IntegerField(default=0)   # 싫어요
    
class UserData(models.Model):
    user_data_seq     = models.AutoField(primary_key=True)
    restaurant_id     = models.IntegerField()
    user_id           = models.TextField()
    name              = models.TextField()   # 맛집 이름
    road_address      = models.TextField()   # 도로명주소
    phone_number      = models.TextField()   # 전화번호
    img_url           = models.TextField()   # img 주소
    comment           = models.TextField()   # 댓글 모음
    restaurant_type   = models.TextField()   # 맛집 유형(카페, 음식점)
    created_at        = models.DateTimeField(auto_now=True)
    
class UserTagLog(models.Model):
    user_log_seq      = models.AutoField(primary_key=True)
    user_id           = models.TextField()
    name              = models.TextField()   # 맛집 이름
    road_address      = models.TextField()   # 도로명주소
    tag_name          = models.TextField()   # 관련 태그
    confidence        = models.FloatField()  # 태그 신뢰정보 (0)
    preference        = models.FloatField()  # 더블 클릭 로그
    created_at        = models.DateTimeField(auto_now=True)

