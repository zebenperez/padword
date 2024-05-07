from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 
from django.urls import reverse

from padword.commons import show_exc, get_or_none, get_param, reverse_cardkey, set_session
from padword.decorators import group_required
from .models import Room
from .models_lock import *
from .lock_lib import ShLock, get_record_type

from datetime import datetime, timedelta


def get_date(dic, key_date, key_time, offset=""):
    date = get_param(dic, key_date)
    time = get_param(dic, key_time)
    #time = key_time
    default = datetime.now() + offset if offset != "" else datetime.now()
    return datetime.strptime("{} {}".format(date, time), "%Y-%m-%d %H:%M") if date != "" and time != "" else default

def get_lock_items(request, project_uuid):
    kwargs = {'project_uuid': project_uuid, 'private': False, 'box': True}

    if "room_search" in request.session and request.session["room_search"] != "":
        #value = request.session["room_search"]
        #room_list = Room.objects.filter(Q(number__icontains = value) | Q(alias__icontains = value)).values_list('number', flat=True)
        #kwargs["room__in"] = room_list
        kwargs["alias__icontains"] = request.session["room_search"] 

    lock_list = list(Lock.objects.filter(**kwargs))
    return lock_list 

def get_context(request, project):
    context = {}
    now = datetime.now()
    context["project"] = project
    context["items"] = get_lock_items(request, project.uuid)
    context["lock_group_list"] = LockGroup.objects.filter(project_uuid=project.uuid)
    context["ini_date"] = now
    context["end_date"] = now + timedelta(days=7)
    return context

'''
    Boxes for "projects" users
'''
@group_required("projects")
def boxes_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        context = get_context(request, project)
        context["project"] = project
        context["active"] = 'box'
        return render(request, "web/boxes-by-project/boxes.html", context)
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("projects")
def box_card_by_project(request):
    try:
        item = get_or_none(Lock, request.GET["obj_id"])
        return render(request, "web/boxes-by-project/box-card.html", {'item': item})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def box_form_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        obj = get_or_none(Lock, request.GET["obj_id"])  
        group_list = LockGroup.objects.filter(project_uuid = project.uuid)
        return render(request, "web/boxes-by-project/box-form.html", {'obj': obj, 'group_list': group_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def box_search_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        set_session(request, "room_search")
        context = get_context(request, project)
        return render(request, "web/boxes-by-project/box-list.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def box_add_code(request):
    try:
        lock = get_or_none(Lock, request.POST["lock_id"])
        radio_code = get_param(request.POST, "radio_code")
        code = reverse_cardkey(get_param(request.POST, "code")) if radio_code == "2" else get_param(request.POST, "code")
        name = get_param(request.POST, "name")
        ini_date = get_date(request.POST, "ini_date", "ini_time")
        end_date = get_date(request.POST, "end_date", "end_time", timedelta(days=7))
        ini_date_gmt = lock.project.gmt_date(ini_date)
        end_date_gmt = lock.project.gmt_date(end_date)

        if code == "":
            msg = _("ERROR: Code must not to be empty!")
        else:
            #errcode = lock.add_card(code, ini_date, end_date, name) if radio_code == "2" else lock.set_code(code, ini_date, end_date, name)
            errcode = ""
            if radio_code == "1":
                errcode = lock.set_code(code, ini_date_gmt, end_date_gmt, name)
                #errcode = lock.set_code(code, ini_date, end_date, name)
            elif radio_code == "2":
                errcode = lock.get_code("3", ini_date_gmt, end_date_gmt, name)
                #errcode = lock.get_code("3", ini_date, end_date, name)
            elif radio_code == "3":
                errcode = lock.add_card(code, ini_date_gmt, end_date_gmt, name) 
                #errcode = lock.add_card(code, ini_date, end_date, name) 
            msg = errcode if "Error" in str(errcode) else _("Code saved!")
            if radio_code == "2":
                msg = "{} <br/> <small>({})</small>".format(msg, errcode)
        return render(request, "web/boxes-by-project/box-code-add.html", {"msg": msg})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})


