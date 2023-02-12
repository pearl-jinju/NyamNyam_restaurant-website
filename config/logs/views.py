#REST 호출이 가능하도록 설정
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponseBadRequest, JsonResponse
from logs.models import SearchLog
import os

# Create your views here.
class SendLog(APIView):
    def post(self, request):
        search_user = request.data.get('user_id')
        print(search_user)
        
        if search_user == "":
            search_user = "guest"
        search_route = request.data.get('search_route')
        search_keyword = request.data.get('search_keyword')

        # search_keyword 유형분석
        if search_keyword[0]=="!":
            search_keyword_type = "restaurant"
        elif search_keyword[0]=="#":
            search_keyword_type = "tag"
        elif search_keyword[0]=="@":
            search_keyword_type = "address"
        else:
            search_keyword_type = "incorrect"
            
        SearchLog.objects.create(
            search_user = search_user,
            search_keyword = search_keyword,
            search_keyword_type = search_keyword_type,
            search_route = search_route
        )
        
        return Response(status=200)
            
        

