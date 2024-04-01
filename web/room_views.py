from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from padword.commons import show_exc, get_or_none, get_param, get_random_str, new_ui_slug, translate, reverse_cardkey, set_session
from padword.decorators import group_required
from .models import *
from .models_lock import *

from datetime import datetime, timedelta
import os
import requests


def get_projects(request):
    search_value = request.session["room_search_name"] if "room_search_name" in request.session else ""
    list_rooms = []
    projects = Project.objects.filter(name__icontains=search_value) if search_value != "" else Project.objects.all()
    #for project in projects:
    #    list_rooms.append([project, Room.objects.filter(parent__isnull = True, project_uuid = project.uuid)])
    #return list_rooms
    return projects

@group_required("admins")
def rooms (request):
    #list_rooms = get_room_items(request)
    return render (request, "web/rooms/rooms.html", {'list_projects': get_projects(request), 'active': 'rooms'})

@group_required("admins")
def room_list (request):
    return render (request, "web/rooms/rooms-list.html", {'list_projects': get_projects(request)})

@group_required("admins")
def rooms_search (request):
    set_session(request, "room_search_name")
    #list_rooms = get_room_items(request)
    #return render (request, "web/rooms/rooms-list.html", {'list_rooms':list_rooms})
    return render (request, "web/rooms/rooms-list.html", {'list_projects': get_projects(request)})

#@group_required("admins")
#def room_form(request):
#    try:
#        project = get_or_none(Project, request.GET["project"], field='uuid') if "project" in request.GET else None
#        #obj = get_or_none(Room, request.GET["obj_id"]) if "obj_id" in request.GET else Room.objects.create(uuid = new_ui_slug(Room))
#        obj = get_or_none(Room, request.GET["obj_id"]) if "obj_id" in request.GET else Room.objects.create(uuid = new_ui_slug(Room), project_uuid=project.uuid)
#        obj.save()
#        if project is None:
#            project = Project.objects.get(uuid=obj.project_uuid)
#        projects = Project.objects.filter(pk=project.pk)
#        floors = Room.objects.filter(parent = None, project_uuid = project.uuid).exclude(pk=obj.pk)
#
#        return render(request, "web/rooms/room-form.html", {'obj': obj, 'projects':projects, 'floors':floors})
#    except Exception as e:
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def room_form(request):
    try:
        #project = get_or_none(Project, request.GET["project"], field='uuid') if "project" in request.GET else None
        project_uuid = get_param(request.GET, "project")
        if "obj_id" in request.GET:
            obj = get_or_none(Room, request.GET["obj_id"])  
        else:
            obj = Room.objects.create(uuid = new_ui_slug(Room), project_uuid=project_uuid)
        group_list = LockGroup.objects.filter(project_uuid = project_uuid)

        return render(request, "web/rooms/room-form.html", {'obj': obj, 'group_list': group_list})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def room_remove(request):
    obj = get_or_none(Room, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        lock_list = Lock.get_locks_by_room(obj)
        obj.unassign_locks(lock_list)
        obj.delete()
    #list_rooms = get_room_items(request)
    #return render (request, "web/rooms/rooms-list.html", {'list_rooms':list_rooms})
    return render (request, "web/rooms/rooms-list.html", {'list_projects': get_projects(request)})

@group_required("admins")
def room_set_group(request):
    try:
        obj = get_or_none(Room, request.GET["obj_id"])
        val = get_param(request.GET, "value")
        if obj != None:
            obj.lock_group_uuid = val
            obj.save()
            lock_list = Lock.get_locks_by_room(obj)
            obj.set_locks_group(val, lock_list)
            return HttpResponse("")
        return HttpResponse(_("Error, room not found!"))
    except Exception as e:
        print(e)
        return HttpResponse("Error, {}".format(str(e)))

@group_required("admins")
def room_multiple(request):
    try:
        project = get_or_none(Project, get_param(request.GET, "project"), "uuid")
        group_list = LockGroup.objects.filter(project_uuid = project.uuid)
        return render(request, "web/rooms/room-multiple.html", {'project': project, 'group_list': group_list})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def room_multiple_save(request):
    try:
        project = get_or_none(Project, get_param(request.POST, "project_uuid"), "uuid")
        order = get_int(request.POST["order"])
        alias = request.POST["alias"]
        number = get_int(request.POST["number"])
        end_number = get_int(request.POST["end_number"])
        #group = request.POST["lock_group_uuid"]
        
        j = 0
        for i in range(number, end_number):
            print(i)
            obj = Room.objects.create(uuid = new_ui_slug(Room), project_uuid=project.uuid)
            obj.order = order + j
            obj.alias = alias
            obj.number = i
            #obj.group = 
            obj.save()
            j += 1
        return redirect("rooms")
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


#@group_required("admins")
#def room_floors(request):
#    project_uuid = request.GET["project"]
#    project = Project.objects.get(uuid=project_uuid)
#    items = Room.objects.filter(parent__isnull = True, project_uuid=project_uuid)
#    return render(request, "web/rooms/rooms-list-details.html", {'items': items,'project':project})

#@group_required("admins")
#def room_search(request):
#    try:
#        filters_to_search = ["alias__icontains", ]
#        items = Room.objects.none()
#        for myfilter in filters_to_search:
#            kwargs = {}
#            if "s-alias" in request.GET and request.GET["s-alias"] != "":
#                kwargs[myfilter] = request.GET["s-alias"]
#            items = items.union(Room.objects.filter(**kwargs))
#        return render(request, "web/rooms/rooms-list-details.html", {'items': items,})
#    except Exception as e:
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})
#
'''
    Locks
'''
def get_date(dic, key_date, key_time, offset=""):
    date = get_param(dic, key_date)
    time = get_param(dic, key_time)
    default = datetime.now() + offset if offset != "" else datetime.now()
    return datetime.strptime("{} {}".format(date, time), "%Y-%m-%d %H:%M") if date != "" and time != "" else default

@group_required("admins", "projects")
def room_lock_details(request):
    try:
        lock = get_or_none(Lock, request.GET["obj_id"])
        now = datetime.now()
        return render(request, "web/rooms/lock-details.html", {'obj': lock, 'ini_date': now, 'end_date': now+timedelta(days=7)})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def room_lock_list(request):
    items = Lock.objects.filter(project_uuid="", room="")
    return render(request, "web/rooms/lock-list.html", {'items': items, 'obj_id': request.GET["obj_id"]})

@group_required("admins", "projects")
def room_lock_add_card(request):
    try:
        lock = get_or_none(Lock, request.POST["lock_id"])
        code = reverse_cardkey(get_param(request.POST, "code"))
        name = get_param(request.POST, "name")
        ini_date = get_date(request.POST, "ini_date", "ini_time")
        end_date = get_date(request.POST, "end_date", "end_time", timedelta(days=7))
        permanent = get_param(request.POST, "permanent")

        msg = ""
        if code != "":
            if permanent == "":
                errcode = lock.add_card(code, ini_date, end_date, name)
            elif permanent != "":
                errcode = lock.add_card(code, ini_date, datetime(2099, 12, 31), name)
            msg = errcode if "Error" in str(errcode) else ""
        else:
            msg = _("ERROR: Code must not to be empty!")
        return render(request, "web/rooms/lock-details-cards.html", {"obj": lock, "msg": msg})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def room_lock_remove_card(request):
    try:
        lock = get_or_none(Lock, request.GET["obj_id"])
        card_id = request.GET["card_id"]

        errcode = lock.remove_card(card_id)
        return render(request, "web/rooms/lock-details-cards.html", {"obj": lock})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def room_lock_add_code(request):
    try:
        lock = get_or_none(Lock, request.POST["lock_id"])
        code = get_param(request.POST, "code")
        name = get_param(request.POST, "name")
        ini_date = get_date(request.POST, "ini_date", "ini_time")
        end_date = get_date(request.POST, "end_date", "end_time", timedelta(days=7))
        permanent = get_param(request.POST, "permanent")
        one = get_param(request.POST, "one")

        msg = ""
        errcode = ""
        if permanent == "" and one == "" and code != "":
            errcode = lock.set_code(code, ini_date, end_date, name)
        elif permanent != "" and code != "":
            errcode = lock.set_code(code, ini_date, datetime(2099, 12, 31), name)
        elif permanent != "" and code == "":
            errcode = lock.get_code(2, ini_date, datetime(2099, 12, 31))
        elif one != "":
            errcode = lock.get_code(1, ini_date, end_date)
        msg = errcode if "Error" in str(errcode) else ""
        return render(request, "web/rooms/lock-details-codes.html", {"obj": lock, "msg": msg})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def room_lock_remove_code(request):
    try:
        lock = get_or_none(Lock, request.GET["obj_id"])
        code_id = request.GET["code_id"]

        errcode = lock.remove_code(code_id)
        msg = errcode if "Error" in str(errcode) else ""
        return render(request, "web/rooms/lock-details-codes.html", {"obj": lock, "msg": msg})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def room_lock_add_ekey(request):
    try:
        lock = get_or_none(Lock, request.POST["lock_id"])
        prefix = get_param(request.POST, "prefix")
        username = get_param(request.POST, "username")
        key_name = get_param(request.POST, "key_name")
        ini_date = get_date(request.POST, "ini_date", "ini_time")
        end_date = get_date(request.POST, "end_date", "end_time", timedelta(days=7))
        permanent = get_param(request.POST, "permanent")

        msg = ""
        if username != "" and key_name != "":
            if permanent == "":
                errcode = lock.add_ekey(username, key_name, ini_date, end_date)
            elif permanent != "":
                errcode = lock.add_ekey(username, key_name, ini_date, datetime(2099, 12, 31))
            if "Error" in str(errcode):
                msg = errcode  
            else:
                lockEkey = LockEkey.objects.create(token=get_random_str(8), username=username, key_name=key_name, ini_date=ini_date, end_date=end_date, lock_uuid=lock.uuid, ekey_id = str(errcode))
        else:
            msg = _("ERROR: Code must not to be empty!")
        return render(request, "web/rooms/lock-details-ekeys.html", {"obj": lock, "msg": msg})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


@group_required("admins", "projects")
def room_lock_remove_ekey(request):
    try:
        lockEkey = get_or_none(LockEkey, request.GET["obj_id"])
        lock = lockEkey.lock

        errcode = lockEkey.lock.remove_ekey(lockEkey.ekey_id)
        msg = errcode if "Error" in str(errcode) else ""
        lockEkey.delete()

        return render(request, "web/rooms/lock-details-ekeys.html", {"obj": lock, "msg": msg})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

def ekey_url(request, token):
    try:
        lockEkey = get_or_none(LockEkey, token, "token")
        return render(request, "web/rooms/ekey_links/{}_ekey.html".format(lockEkey.lock.project.name[:4].lower()), {"obj": lockEkey.lock,})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


'''
    Rooms by project
'''
@group_required("admins", "projects")
def rooms_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        return render(request, "web/rooms-by-project/rooms.html", {'project': project, 'active': 'rooms'})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def room_list_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        return render(request, "web/rooms-by-project/rooms-list.html", {'project': project})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def room_form_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        obj = get_or_none(Room, request.GET["obj_id"])  
        group_list = LockGroup.objects.filter(project_uuid = project.uuid)
        return render(request, "web/rooms-by-project/room-form.html", {'obj': obj, 'group_list': group_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


