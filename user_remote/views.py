from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate
from padword.decorators import group_required
from .models import *

# Create your views here.

def users(request):
    items = PWUser.objects.all()
    return render(request, 'users/list.html', {'items':items})

def user_search(request):
    pass

