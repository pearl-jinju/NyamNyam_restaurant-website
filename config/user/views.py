from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User
from django.contrib.auth.hashers import make_password #단방향 암호화 툴

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
        print(nickname)
        print(email)
        print(password)
        print(password_check)
        
        if password!=password_check:
            return Response(status=400)
        
        # DB에 넣기 
        User.objects.create(
            nickname=nickname,
            email=email,
            password=make_password(password),
            grade='-',
            profile_img = "defualt_profile.jpg"
            )
        return Response(status=200)
    
class Login(APIView):
    def get(self, request):
        return render(request, "user/login.html")
    def post(self, request):
        # TODO 로그인
        pass

    