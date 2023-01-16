from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

# Create your models here.
class User(AbstractBaseUser):
    """
    유저 프로파일 사진
    유저 아이디 닉네임(화면에 표기되는 이름)
    유저 이메일 주소 회원가입할떄 사용하는 아이디
    유저 비밀번호  -defualt
    """ 
    profile_img = models.TextField()
    nickname = models.CharField(max_length=24, unique=True)  # nickname은 겹칠 수 없음
    email = models.EmailField(unique=True)  # 이메일은 겹칠 수 없음
    grade = models.TextField()  # 등급 필드 , 게시물의 수 및 좋아요 비율에 따라 차등부여
    
    # 어떤 필드를 유저의 이름으로 쓸것인지 결정
    USERNAME_FIELD ="nickname"
    
    class Meta:
        db_table ="User"
     

