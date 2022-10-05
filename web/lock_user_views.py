from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate, set_session, get_random_str
from padword.decorators import group_required
from .models import *
from .lock_lib import ShLock

import requests, time, datetime, hashlib, json


'''
    Locks
'''
def get_lock_user_items(request):
    kwargs = {}

    if "lock_user_search_username" in request.session and request.session["lock_user_search_username"] != "":
        kwargs["username__icontains"] = request.session["lock_search_username"]
    if "lock_user_search_project" in request.session and request.session["lock_user_search_project"] != "":
        project_uuid_list = [item.uuid for item in Project.objects.filter(name__icontains=request.session["lock_user_search_project"])]
        kwargs["project_uuid__in"] = project_uuid_list

    return LockUser.objects.filter(**kwargs) if len(kwargs) > 0 else LockUser.objects.all()

def get_context(request):
    lock_items = LockUser.list_user_not_assigned()
    items = get_lock_user_items(request)
    return {'items':items, 'lock_items': lock_items}

@group_required("admins")
def locks_users(request):
    try:
        context = get_context(request)
        return render (request, "web/locks-users/locks-users.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def lock_user_search(request):
    try:
        set_session(request, "lock_user_search_username")
        set_session(request, "lock_user_search_project")
        context = get_context(request)
        return render(request, "web/locks-users/lock-user-list.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def lock_user_form(request):
    obj_id = get_param(request.GET, "obj_id")
    obj = get_or_none(LockUser, obj_id) if obj_id != "" else LockUser.objects.create(uuid = new_ui_slug(LockUser))
    return render(request, "web/locks-users/lock-user-form.html", {'obj': obj})

@group_required("admins")
def lock_user_set_password(request):
    try:
        passwd = get_param(request.GET, "value")
        obj_id = get_param(request.GET, "obj_id")
        obj = get_or_none(LockUser, obj_id)
        if obj != None:
            obj.password = passwd
            obj.lock_password = hashlib.md5(passwd.encode()).hexdigest()
            obj.save()
        return HttpResponse("")
    except Exception as e:
        return HttpResponse("Error: {}".format(show_exc(e)))

@group_required("admins")
def lock_user_register(request):
    try:
        obj_id = get_param(request.GET, "obj_id")
        obj = get_or_none(LockUser, obj_id)
        if obj != None:
            username = obj.create_lock_user()
            print(username)
            if "Error" not in str(username):
                obj.lock_username = username
                obj.save()
        context = get_context(request)
        return render(request, "web/locks-users/lock-user-list.html", context)
    except Exception as e:
        return HttpResponse("Error: {}".format(show_exc(e)))

@group_required("admins")
def lock_user_remove(request):
    obj = get_or_none(LockUser, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete_lock_user()
        obj.delete()
    context = get_context(request)
    return render (request, "web/locks-users/lock-user-list.html", context)

@group_required("admins")
def lock_user_remove_by_username(request):
    try:
        username = get_param(request.GET, "username")
        err = json.load(LockUser.delete_user_by_username(username))
        msg = err["errmsg"] if err["errcode"] != 0 else ""
    except Exception as e:
        print(e)
        msg = e

    context = get_context(request)
    context["msg"] = msg
    return render (request, "web/locks-users/lock-user-list.html", context)

