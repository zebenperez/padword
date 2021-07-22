from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import *
from django.core import serializers
from padword.commons import show_exc, get_or_none


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
def projects(request, company_id = None):
    try:
        company = get_or_none(Company, company_id)
        if company is None:
            items = Project.objects.all()
        else:
            items = Project.objects.filter(company = company)
        return render(request, "web/projects/projects.html", {'items':items, 'company': company})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

def project_search(request):
    try:
        kwargs = {}
        if request.GET["s-name"] != "":
            kwargs["name__icontains"] = request.GET["s-name"]
        if request.GET["s-comp"] != "":
            kwargs["company__id"] = request.GET["s-comp"]
        items = Project.objects.filter(**kwargs)
        if request.GET["s-comp"] == "":
            kwargs = {}
            if request.GET["s-name"] != "":
                kwargs["company__name__icontains"] = request.GET["s-name"]
                items = items.union(Project.objects.filter(**kwargs))
        return render(request, "web/projects/project-list.html", {'items': items,})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

def project_form(request):
    obj = get_or_none(Project, request.GET["obj_id"]) if "obj_id" in request.GET else Project.objects.create()
    return render(request, "web/projects/project-form.html", {'obj': obj, 'companies': Company.objects.all()})

def project_remove(request):
    obj = get_or_none(Project, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    items = Project.objects.all()
    return render (request, "web/projects/project-list.html",{'items':items} )


'''
    Channels
'''
def channels(request, project_id=None, company_id=None):
    try:
        print ('{} - {}'.format(project_id, company_id))
        if project_id is not None:
            items = Channel.objects.filter(project__pk = project_id)
        elif company_id is not None:
            items = Channel.objects.filter(project__company__pk = company_id)
        else:
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
        items = Company.objects.all()
        return render (request, "web/companies/companies.html",{'items':items} )
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

def company_search(request):
    try:
        filters_to_search = ["name__icontains", ]
        items = Company.objects.none()
        for myfilter in filters_to_search:
            kwargs = {}
            if "s-name" in request.GET and request.GET["s-name"] != "":
                kwargs[myfilter] = request.GET["s-name"]
            items = items.union(Company.objects.filter(**kwargs))
        return render(request, "web/companies/company-list.html", {'items': items,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

def company_form(request):
    obj = get_or_none(Company, request.GET["obj_id"]) if "obj_id" in request.GET else Company.objects.create()
    return render(request, "web/companies/company-form.html", {'obj': obj,})

def company_remove(request):
    obj = get_or_none(Company, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    items = Company.objects.all()
    return render (request, "web/companies/company-list.html",{'items':items} )

'''
    Devices
'''
def devices(request, project_id = None, company_id = None, channel_id = None):
    try:
        if project_id is not None:
            items= Device.by_project(Project.objects.filter(pk = project_id))
        elif company_id is not None:
            items= Device.by_company(Company.objects.filter(pk = company_id))
        elif channel_id is not None:
            items= Device.by_channel(Channel.objects.filter(pk = channel_id))
        else:
            items= Device.objects.all()
        return render (request, "web/devices.html",{'items':items} )
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

def device_search(request):
    try:
        filters_to_search = ["imei__icontains", "serial_number__icontains", "room__icontains", "alias__icontains"]
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
