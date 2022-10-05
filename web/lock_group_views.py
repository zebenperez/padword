from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate, set_session, get_random_str
from padword.decorators import group_required
from .models import *
from .lock_lib import ShLock

import requests, time, datetime, hashlib, json


'''
    Lock groups
'''
def get_lock_group_items(request, project):
    kwargs = {'project_uuid': project.uuid}

    if "lock_group_search_name" in request.session and request.session["lock_group_search_name"] != "":
        kwargs["name__icontains"] = request.session["lock_group_search_name"]

    return LockGroup.objects.filter(**kwargs)
    #return LockGroup.objects.filter(**kwargs) if len(kwargs) > 0 else LockGroup.objects.all()

def get_context(request, project):
    group_items = LockGroup.list_group_not_assigned(project.lock_access_token)
    items = get_lock_group_items(request, project)
    return {'items':items, 'group_items': group_items}

@group_required("admins")
#def locks_groups(request):
def locks_groups_by_project(request, project_id):
    try:
        project = get_or_none(Project, project_id)
        context = get_context(request, project)
        context["project"] = project
        return render (request, "web/locks-groups/locks-groups.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def lock_group_search(request):
    try:
        set_session(request, "lock_group_search_name")
        context = get_context(request)
        return render(request, "web/locks-groups/lock-group-list.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def lock_group_form(request):
    obj_id = get_param(request.GET, "obj_id")
    project_uuid = get_param(request.GET, "project_uuid")
    obj = get_or_none(LockGroup, obj_id) if obj_id != "" else LockGroup.objects.create(uuid = new_ui_slug(LockGroup), project_uuid=project_uuid)
    return render(request, "web/locks-groups/lock-group-form.html", {'obj': obj})

@group_required("admins")
def lock_group_save(request):
    try:
        value = get_param(request.POST, "name")
        project_uuid = get_param(request.POST, "project_uuid")
        obj_id = get_param(request.POST, "obj_id")

        project = get_or_none(Project, project_uuid, "uuid")
        obj = get_or_none(LockGroup, obj_id)

        if obj != None and project != None:
            obj.name = value
            obj.remote_name = "{} {}".format(project.name, value)
            obj.project_uuid = project_uuid
            obj.save()
            obj.remote_id = obj.create_lock_group()
            obj.save()
        context = get_context(request, project)
        return render(request, "web/locks-groups/lock-group-list.html", context)
    except Exception as e:
        print(e)
        return HttpResponse("Error: {}".format(show_exc(e)))

@group_required("admins")
def lock_group_remove(request):
    obj = get_or_none(LockGroup, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        Room.objects.filter(lock_group_uuid=obj.uuid).update(lock_group_uuid='')
        obj.delete_lock_group()
        obj.delete()
    context = get_context(request)
    return render (request, "web/locks-groups/lock-group-list.html", context)

@group_required("admins")
def lock_group_remove_by_id(request):
    try:
        group_id = get_param(request.GET, "group_id")
        err = json.load(LockGroup.delete_group_by_id(group_id))
        msg = err["errmsg"] if err["errcode"] != 0 else ""
    except Exception as e:
        print(e)
        msg = e

    context = get_context(request)
    context["msg"] = msg
    return render (request, "web/locks-groups/lock-group-list.html", context)

