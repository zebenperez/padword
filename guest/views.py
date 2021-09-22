from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.shortcuts import render, redirect
import datetime

from .models import *
from padword.commons import show_exc, get_or_none, new_ui_slug, translate
from padword.decorators import group_required
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
@group_required("admins")
def guests(request):
    try:
        #items= Guest.objects.filter(check_out__gte = datetime.datetime.now())
        items= Guest.objects.all()
        total_count = items.count()


        return render (request, "guest/guests.html",{'items':items[0:20], 'page':0, 'n_items':total_count})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins")
def guest_search(request):
    try:
        filters_to_search = ["name__icontains", "room__icontains", "surname__icontains"]
        search_value = request.GET["s-name"] if "s-name" in request.GET else ""
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
            #items = Guest.objects.filter(check_out__gte = datetime.datetime.today())
            items = Guest.objects.all()
        return render(request, "guest/guest-list.html", {'items': items,})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins")
def guest_form(request):
    try:
        obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else Guest.objects.create(UUID = new_ui_slug(Guest))
        return render(request, "guest/guest-form.html", {'obj': obj,})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def guest_remove(request):
    obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()

    items = Guest.objects.all()
    return render(request, "guest/guest-list.html", {'items':items,})

@group_required("admins","projects")
def guest_pagination(request, page=0):
    try:
        items = Guest.objects.all()
        items = items[page*20:(page+1)*20]
        return render(request, "guest/guest-page.html", {'items':items, 'page':page})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

'''
    Devices
'''
@group_required("admins", "projects")
def devices(request):
    try:
        items= Guest.objects.all()
        total_count = items.count()

        return render (request, "device/devices.html",{'items':items[0:20], 'page':0, 'n_items':total_count})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

#@group_required("admins")
#def guest_search(request):
#    try:
#        filters_to_search = ["name__icontains", "room__icontains", "surname__icontains"]
#        search_value = request.GET["s-name"] if "s-name" in request.GET else ""
#        if search_value != "":
#            items = Guest.objects.none()
#            for myfilter in filters_to_search:
#                kwargs = {}
#                kwargs[myfilter] = search_value
#                items = items.union(Guest.objects.filter(**kwargs))
#
#            channels = webmod.Channel.objects.filter(name__icontains = search_value)
#            items = items.union(Guest.by_channel(channels))
#            projects = webmod.Project.objects.filter(name__icontains = search_value)
#            items = items.union(Guest.by_project(projects))
#        else:
#            #items = Guest.objects.filter(check_out__gte = datetime.datetime.today())
#            items = Guest.objects.all()
#        return render(request, "guest/guest-list.html", {'items': items,})
#    except Exception as e:
#        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})
#
#@group_required("admins")
#def guest_form(request):
#    try:
#        obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else Guest.objects.create(UUID = new_ui_slug(Guest))
#        return render(request, "guest/guest-form.html", {'obj': obj,})
#    except Exception as e:
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})
#
#@group_required("admins")
#def guest_remove(request):
#    obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else None
#    if obj != None:
#        obj.delete()
#
#    items = Guest.objects.all()
#    return render(request, "guest/guest-list.html", {'items':items,})
#
#@group_required("admins","projects")
#def guest_pagination(request, page=0):
#    try:
#        items = Guest.objects.all()
#        items = items[page*20:(page+1)*20]
#        return render(request, "guest/guest-page.html", {'items':items, 'page':page})
#    except Exception as e:
#        return render(request, "error_exception.html", {'exc':show_exc(e)})
