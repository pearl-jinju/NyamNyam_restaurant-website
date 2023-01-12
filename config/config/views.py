from django.shortcuts import render
from rest_framework.views import APIView

#REST 호출이 가능하도록 설정
class Sub(APIView):
    def get(self, request):
        print("GET")
        return render(request,"nyam\main.html")

    def post(self, request):
        print("POST")
        return render(request,"nyam\main.html")

