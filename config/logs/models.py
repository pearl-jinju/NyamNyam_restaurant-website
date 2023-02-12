from django.db import models

# Create your models here.
class SearchLog(models.Model):
    log_id               = models.IntegerField(primary_key=True) # log id 
    search_user          = models.TextField()   # 검색 유저명(guest or user nickname)
    search_keyword       = models.TextField()   # 검색어
    search_keyword_type  = models.TextField()   # 검색어 유형(맛집명,태그,주소,오류)
    search_route         = models.TextField()   # 검색 방법 (검색창,버튼 클릭)
    created_at           = models.DateTimeField(auto_now=True)