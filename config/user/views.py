from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User
from django.contrib.auth.hashers import make_password #단방향 암호화 툴
import re

# Create your views here.
class Join(APIView):
    def get(self, request):
        return render(request, "user/join.html")
    def post(self, request):
        # TODO 회원가입
        nickname = request.data.get('nickname',None)
        email = request.data.get('email',None)
        password = request.data.get('password',None)
        password_check = request.data.get('password_check',None)
        
        
        # 이메일 형식 확인
        pattern = re.compile('^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        if pattern.match(email)!= None:
            pass
        else:
            return Response(status=400,data=dict(message="이메일 형식이 잘못되었습니다."))

       # 비밀번호 및 확인 비밀번호 확인
        if password!=password_check:
            return Response(status=400,data=dict(message="비밀번호가 같지 않습니다."))
        
        # 비밀번호 최소길이 확인
        if (len(password)<8)or(len(password_check)<8):
            return Response(status=400,data=dict(message="비밀번호는 최소 8자 이상입니다."))
        
        # DB에 넣기 
        User.objects.create(
            nickname=nickname,
            email=email,
            password=make_password(password),
            grade='-',
            profile_img = "https://audition.hanbiton.com/images/common/img_default.jpg"
            )
        return Response(status=200)
    
    
class LogIn(APIView):
    def get(self, request):
        return render(request, "user/login.html")
    def post(self, request):
        # TODO 로그인
        email = request.data.get('email',None)
        password = request.data.get('password',None)
        
        user_data = User.objects.filter(email=email).first()   #쿼리셋(리스트)에서 첫번째를 지정하여 값으로

        if user_data is None:
            # 해킹 방지를 위한 중의적 메세지 출력
            return Response(status=400, data=dict(message="이메일 또는 비밀번호가 올바르지 않습니다"))
        
        if user_data.check_password(password):
            # 로그인 성공, 세션 또는 쿠키에 넣는다
            request.session['email']=email
            return Response(status=200)
        else:
            # 해킹 방지를 위한 중의적 메세지 출력
            return Response(status=400, data=dict(message="이메일 또는 비밀번호가 올바르지 않습니다"))            
        
class LogOut(APIView):
    def get(self, request):
        # 세션 삭제
        request.session.flush()
        return render(request, "user/login.html")