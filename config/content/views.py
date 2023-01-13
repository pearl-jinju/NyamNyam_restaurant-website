from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Feed
import pandas as pd
import random
from ast import literal_eval

# Create your views here.

 