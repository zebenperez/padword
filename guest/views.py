from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import *
from django.core import serializers

from padword.commons import show_exc


# Create your views here.

def index(request):
    try:
        guests = Guest.objects.all()
        registers = [{'name':comp.name,'surname':comp.surname} for comp in guests]

        return JsonResponse({'results':registers, 'error':0})
        #return JsonResponse({'results':serializers.serialize("json", companies, fields=('uuid','name')), 'error':0})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})
