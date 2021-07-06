from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import *
from django.core import serializers
from padword.commons import show_exc


# Create your views here.

def index(request):
    try:
        return render (request, "base_nestor.html")
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

def channel_search(request):
    try:
        filters_to_search = ["name__icontains", "project__name__icontains", "project__company__name__icontains"]
        items = Channel.objects.none()
        for myfilter in filters_to_search:
            kwargs = {}
            if request.GET["s-name"] != "":
                kwargs[myfilter] = request.GET["s-name"]
            items = items.union(Channel.objects.filter(**kwargs))
        return render(request, "web/channel-list.html", {'items': items,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

'''
    Companies
'''
def companies(request):
    try:
        items= Company.objects.all()

        return render (request, "web/companies.html",{'items':items} )
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

def company_search(request):
    try:
        filters_to_search = ["name__icontains", ]
        items = Company.objects.none()
        for myfilter in filters_to_search:
            kwargs = {}
            if request.GET["s-name"] != "":
                kwargs[myfilter] = request.GET["s-name"]
            items = items.union(Company.objects.filter(**kwargs))
        return render(request, "web/company-list.html", {'items': items,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})
'''
    Devices
'''
def devices(request):
    try:
        items= Device.objects.all()
        return render (request, "web/devices.html",{'items':items} )
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

def device_search(request):
    try:
        filters_to_search = ["imei__icontains", "serial_number__icontains", "room__icontains"]
        search_value = request.GET["s-name"]
        if search_value != "":
            items = Device.objects.none()
            for myfilter in filters_to_search:
                kwargs = {}
                kwargs[myfilter] = search_value
                items = items.union(Device.objects.filter(**kwargs))

            projects = Project.objects.filter(name__icontains = search_value).values_list('uuid')
            items = items.union(Device.objects.filter(project_uuid__in = projects))
            projects = Project.objects.filter(company__in = Company.objects.filter(name__icontains = search_value)).values_list('uuid')
            items = items.union(Device.objects.filter(project_uuid__in = projects))
            channels = Channel.objects.filter(name__icontains = search_value).values_list('uuid')
            items = items.union(Device.objects.filter(channel_id__in = channels ))
        else:
            items = Device.objects.all()
        return render(request, "web/device-list.html", {'items': items,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})
