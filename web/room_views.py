from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 
from django.views.decorators.csrf import csrf_exempt

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate
from padword.decorators import group_required
from .models import *

from django.conf import settings
import os
import requests

@group_required("admins")
def rooms (request):
    projects = Project.objects.all()
    list_rooms = []
    for project in projects:
        list_rooms.append([project, Room.objects.filter(parent__isnull = True, project_uuid = project.uuid)])
    return render (request, "web/rooms/rooms.html", {'list_rooms':list_rooms})

@group_required("admins")
def room_form(request):
    try:
        project = get_or_none(Project, request.GET["project"], field='uuid') if "project" in request.GET else None
        #obj = get_or_none(Room, request.GET["obj_id"]) if "obj_id" in request.GET else Room.objects.create(uuid = new_ui_slug(Room))
        obj = get_or_none(Room, request.GET["obj_id"]) if "obj_id" in request.GET else Room.objects.create(uuid = new_ui_slug(Room), project_uuid=project.uuid)
        obj.save()
        if project is None:
            project = Project.objects.get(uuid=obj.project_uuid)
        projects = Project.objects.filter(pk=project.pk)
        floors = Room.objects.filter(parent = None, project_uuid = project.uuid).exclude(pk=obj.pk)

        return render(request, "web/rooms/room-form.html", {'obj': obj, 'projects':projects, 'floors':floors})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def room_remove(request):
    obj = get_or_none(Room, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    items = Room.objects.filter(parent__isnull = True)
    return render (request, "web/rooms/rooms-list.html",{'items':items} )

@group_required("admins")
def room_floors(request):
    project_uuid = request.GET["project"]
    project = Project.objects.get(uuid=project_uuid)
    items = Room.objects.filter(parent__isnull = True, project_uuid=project_uuid)
    return render(request, "web/rooms/rooms-list.html", {'items': items,'project':project})

@group_required("admins")
def room_search(request):
    try:
        filters_to_search = ["alias__icontains", ]
        items = Room.objects.none()
        for myfilter in filters_to_search:
            kwargs = {}
            if "s-alias" in request.GET and request.GET["s-alias"] != "":
                kwargs[myfilter] = request.GET["s-alias"]
            items = items.union(Room.objects.filter(**kwargs))
        return render(request, "web/rooms/rooms-list.html", {'items': items,})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})
