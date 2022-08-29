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
def keycards (request):
    projects = Project.objects.all()
    list_keycards = []
    for project in projects:
        list_keycards.append([project, KeyCard.objects.filter(project_uuid = project.uuid)])
    return render (request, "web/keycards/keycards.html", {'list_keycards':list_keycards})

@group_required("admins")
def keycard_form(request):
    try:
        project = get_or_none(Project, request.GET["project"], field='uuid') if "project" in request.GET else None
        obj = get_or_none(KeyCard, request.GET["obj_id"]) if "obj_id" in request.GET else KeyCard.objects.create(uuid = new_ui_slug(KeyCard), project_uuid=project.uuid)
        obj.save()
        if project is None:
            project = Project.objects.get(uuid=obj.project_uuid)
        projects = Project.objects.filter(pk=project.pk)
        return render(request, "web/keycards/keycard-form.html", {'obj': obj, 'projects':projects})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def keycard_remove(request):
    obj = get_or_none(KeyCard, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    items = KeyCard.objects.filter(parent__isnull = True)
    return render (request, "web/keycards/keycards-list.html",{'items':items} )

@group_required("admins")
def keycard_floors(request):
    project_uuid = request.GET["project"]
    project = Project.objects.get(uuid=project_uuid)
    items = KeyCard.objects.filter(parent__isnull = True, project_uuid=project_uuid)
    return render(request, "web/keycards/keycards-list.html", {'items': items,'project':project})

@group_required("admins")
def keycard_search(request):
    try:
        filters_to_search = ["alias__icontains", ]
        items = KeyCard.objects.none()
        for myfilter in filters_to_search:
            kwargs = {}
            if "s-alias" in request.GET and request.GET["s-alias"] != "":
                kwargs[myfilter] = request.GET["s-alias"]
            items = items.union(KeyCard.objects.filter(**kwargs))
        return render(request, "web/keycards/keycards-list.html", {'items': items,})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})
