from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponseBadRequest, JsonResponse
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
        
        
        #닉네임 길이 확인
        if (4<=len(nickname)<=16)==False:
            return JsonResponse({"error": "닉네임의 길이는 4자 이상 ~ 16자 이하로 작성해주십시오."}, status=400)
        elif User.objects.filter(nickname=nickname).exists():
            return JsonResponse({"error": "이미 사용중인 닉네임입니다."}, status=400)
        
        # 이메일 형식 확인
        pattern = re.compile('^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        # 1. 중복아이디 확인
        if User.objects.filter(email=email).exists():
            return JsonResponse({"error": "이미 등록된 이메일입니다."}, status=400)
        # 2. 이메일 적합성 확인
        elif pattern.match(email)!= None:
            pass
        else:
            return JsonResponse({"error": "이메일 형식이 잘못되었습니다."}, status=400)

       # 비밀번호 및 확인 비밀번호 확인
        if password!=password_check:
            return JsonResponse({"error": "비밀번호가 같지 않습니다."}, status=400)
        
        # 비밀번호 최소길이 확인
        if (len(password)<8)or(len(password_check)<8):
            return JsonResponse({"error": "비밀번호는 최소 8자 이상입니다."}, status=400)

        #
        
        # DB에 넣기 
        User.objects.create(
            nickname=nickname,
            email=email,
            password=make_password(password),
            grade='-',
            profile_img = "img_default.jpg"
            )
        return Response(status=200)
    
    
class LogIn(APIView):
    def get(self, request):
        return render(request, "user/login.html")
    def post(self, request):
        # TODO 로그인
        email = request.data.get('email',None)
        password = request.data.get('password',None)
        pattern = re.compile('^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        # 이메일 형식 확인
        if pattern.match(email)!= None:
            pass
        else:
            return JsonResponse({"error": "아이디는 이메일 형식(ex. example@gmail.com)입니다."}, status=400)
        
        user_data = User.objects.filter(email=email).first()   #쿼리셋(리스트)에서 첫번째를 지정하여 값으로
        
        #유저 정보 확인
        if user_data is None:
            # 해킹 방지를 위한 중의적 메세지 출력
            return JsonResponse({"error": "아이디 또는 비밀번호가 올바르지 않습니다"}, status=400)
        
        if user_data.check_password(password):
            # 로그인 성공, 세션 또는 쿠키에 넣는다
            request.session['email']=email
            return Response(status=200)
        
        else:
            # 해킹 방지를 위한 중의적 메세지 출력
             return JsonResponse({"error": "아이디 또는 비밀번호가 올바르지 않습니다"}, status=400)         
        
class LogOut(APIView):
    def get(self, request):
        # 세션 삭제
        request.session.flush()
        return render(request, "user/login.html")