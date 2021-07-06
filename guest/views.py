from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import *
from django.core import serializers
import datetime

from padword.commons import show_exc
import web.models as webmod 


# Create your views here.

def index(request):
    try:
        guests = Guest.objects.all()
        registers = [{'name':comp.name,'surname':comp.surname} for comp in guests]

        return JsonResponse({'results':registers, 'error':0})
        #return JsonResponse({'results':serializers.serialize("json", companies, fields=('uuid','name')), 'error':0})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

'''
    Guests
'''
def guests(request):
    try:
        items= Guest.objects.filter(check_out__gte = datetime.datetime.now())

        return render (request, "guest/guests.html",{'items':items} )
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

def guest_search(request):
    try:
        filters_to_search = ["name__icontains", "room__icontains", "surname__icontains"]
        search_value = request.GET["s-name"]
        if search_value != "":
            items = Guest.objects.none()
            for myfilter in filters_to_search:
                kwargs = {}
                kwargs[myfilter] = search_value
                items = items.union(Guest.objects.filter(**kwargs))

            channels = webmod.Channel.objects.filter(name__icontains = search_value)
            items = items.union(Guest.by_channel(channels))
            projects = webmod.Project.objects.filter(name__icontains = search_value)
            items = items.union(Guest.by_project(projects))
        else:
            items = Guest.objects.filter(check_out__gte = datetime.datetime.today())
        return render(request, "guest/guest-list.html", {'items': items,})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

