from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import *
from django.core import serializers
from padword.commons import show_exc


# Create your views here.

def index(request):
    try:
        companies = Company.objects.all()
        registers = [{'name':comp.name,'uuid':comp.uuid} for comp in companies]

        return render (request, "web/index.html",{'items':registers} )
        return JsonResponse({'results':registers, 'error':0})
        #return JsonResponse({'results':serializers.serialize("json", companies, fields=('uuid','name')), 'error':0})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

'''
    Projects
'''
def projects(request):
    try:
        items= Project.objects.all()

        return render (request, "web/projects.html",{'items':items} )
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

def project_search(request):
    try:
        kwargs = {}
        if request.GET["s-name"] != "":
            kwargs["name__icontains"] = request.GET["s-name"]
        items = Project.objects.filter(**kwargs)
        kwargs = {}
        if request.GET["s-name"] != "":
            kwargs["company__name__icontains"] = request.GET["s-name"]
        items = items.union(Project.objects.filter(**kwargs))
        return render(request, "web/project-list.html", {'items': items,})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})


'''
    Channels
'''
def channels(request):
    try:
        items= Channel.objects.all()

        return render (request, "web/channels.html",{'items':items} )
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

def companies(request):
    try:
        items= Company.objects.all()

        return render (request, "web/companies.html",{'items':items} )
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

def devices(request):
    try:
        items= Device.objects.all()
        return render (request, "web/devices.html",{'items':items} )
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

