from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate, set_session, reverse_cardkey
from padword.decorators import group_required
from .models import *
from .lock_lib import ShLock
from guest.models import KeyCode, KeyCard

import requests
import time, datetime


'''
    Locks
'''
def remove_lock(lock):
    KeyCode.objects.filter(lock=lock.uuid).delete()
    KeyCard.objects.filter(lock=lock.uuid).delete()
    lock.delete()


def update_locks(project):
    sh_lock = ShLock(project.lock_access_token)

    #for item in sh_lock.get_lock_all():
    #    print(item)

    current_locks = []
    for item in sh_lock.get_locks():
        Lock.objects.get_or_create(uuid=item, project_uuid=project.uuid)
        if item not in current_locks:
            current_locks.append(item)
    lock_list = Lock.objects.filter(project_uuid=project.uuid).exclude(uuid__in = current_locks)
    for lock in lock_list:
        remove_lock(lock)

#def set_lock_filter_session(request):
#    request.session["lock_search_alias"] = request.GET["s-alias"] if "s-alias" in request.GET and request.GET["s-alias"] else ""

def get_lock_items(request, project_uuid):
    kwargs = {'project_uuid': project_uuid}

    if "lock_search_alias" in request.session and request.session["lock_search_alias"] != "":
        kwargs["alias__icontains"] = request.session["lock_search_alias"]

    return Lock.objects.filter(**kwargs)

    #if "lock_search_project" in request.session and request.session["lock_search_project"] != "":
    #    project_uuid_list = [item.uuid for item in Project.objects.filter(name__icontains=request.session["lock_search_project"])]
    #    kwargs["project_uuid__in"] = project_uuid_list

    #return Lock.objects.filter(**kwargs) if len(kwargs) > 0 else Lock.objects.all()

def get_context(request, project_uuid):
    context = {}
    now = datetime.datetime.now()
    context["items"] = get_lock_items(request, project_uuid)
    context["lock_group_list"] = LockGroup.objects.filter(project_uuid=project_uuid)
    context["ini_date"] = now
    context["end_date"] = now + datetime.timedelta(days=7)
    return context

@group_required("admins")
#def locks(request):
def locks_by_project(request, project_id):
    msg = ""
    project = get_or_none(Project, project_id)
    try:
        update_locks(project)
    except Exception as e:
        print(e)
        msg = e
 
    try:
        context = get_context(request, project.uuid)
        context["project"] = project
        context["msg"] = msg
        return render (request, "web/locks/locks.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def lock_search(request):
    try:
        #set_lock_filter_session(request)
        #set_session(request, "lock_search_project")
        project_uuid = get_param(request.GET, "project_uuid")
        set_session(request, "lock_search_alias")
        context = get_context(request, project_uuid)
        return render(request, "web/locks/lock-list.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def lock_form(request):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/locks/lock-form.html", {'obj': obj,})

@group_required("admins")
def lock_remove(request):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        project_uuid = obj.project_uuid
        #obj.delete()
        remove_lock(obj)
    context = get_context(request, project_uuid)
    return render (request, "web/locks/lock-list.html", context)

@group_required("admins")
def lock_get_all_passcodes(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/locks/lock-all-passcodes.html", {'obj': obj,})

@group_required("admins")
def lock_remove_code(request):
    try:
        lock = get_or_none(Lock, request.GET["obj_id"])
        code_id = request.GET["code_id"]

        errcode = lock.remove_code(code_id)
        msg = errcode if "Error" in str(errcode) else ""
 
        return HttpResponse("")
        #return render(request, "web/locks/lock-all-cards.html", {'obj': lock,})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


@group_required("admins")
def lock_get_all_cards(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/locks/lock-all-cards.html", {'obj': obj,})

@group_required("admins")
def lock_remove_card(request):
    try:
        lock = get_or_none(Lock, request.GET["obj_id"])
        card_id = request.GET["card_id"]

        errcode = lock.remove_card(card_id)
        return HttpResponse("")
        #return render(request, "web/locks/lock-all-cards.html", {'obj': lock,})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


@group_required("admins")
def lock_set_action(request):
    try:
        msg = ""
        errcode = ""

        project_uuid = get_param(request.POST, "project_uuid")
        action = get_param(request.POST, "action")

        value = get_param(request.POST, "value")

        code = reverse_cardkey(get_param(request.POST, "code")) if action == "2" else get_param(request.POST, "code")
        ini_date = get_param(request.POST, "ini_date", datetime.datetime.now())
        ini_date = datetime.datetime.strptime(ini_date, "%Y-%m-%d") if isinstance(ini_date, str) else ini_date
        end_date = get_param(request.POST, "end_date", datetime.datetime.now() + datetime.timedelta(days=7))
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") if isinstance(end_date, str) else end_date
        permanent = get_param(request.POST, "permanent")

        lock_group_uuid = get_param(request.POST, "lock_group")

        for key in request.POST.keys():
            if "ch_" in key:
                lock = get_or_none(Lock, key.split("_")[1])
                if lock != None:
                    if action == "1":
                        lock.group_uuid = lock_group_uuid
                        lock.save()
                    if action == "2":
                        if permanent == "":
                            errcode = lock.add_card(code, ini_date, end_date)
                        elif permanent != "":
                            errcode = lock.add_card(code, ini_date, datetime(2099, 12, 31))
                    if action == "3":
                        #if permanent == "" and one == "":
                        if permanent == "":
                            errcode = lock.set_code(code, ini_date, end_date)
                        elif permanent != "":
                            errcode = lock.set_code(code, ini_date, datetime(2099, 12, 31))
                        #elif one != "":
                        #    errcode = lock.get_code(1, ini_date, end_date)
                    msg = errcode if "Error" in str(errcode) else ""
                 
        context = get_context(request, project_uuid)
        context["msg"] = msg
        return render(request, "web/locks/lock-list.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

#@group_required("admins")
#def lock_get_cards(request):
#    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
#    url = 'https://euapi.ttlock.com/v3/identityCard/list'
#    if obj is None:
#        list_obj = Lock.objects.all()
#    else:
#        list_obj = [obj]
#
#    for obj in list_obj:
#        params = dict(
#            clientId='c5cd9353990e4061a082a7a275897de1',
#            accessToken='4719a3f737f7d1adafe139fbea20f6fb',
#            lockId=int(obj.uuid),
#            pageNo=1,
#            pageSize=100,
#            date = int(round(datetime.datetime.now().timestamp() * 1000))
#        )
#        resp = requests.get(url=url, params=params)
#        data = resp.json() # Check the JSON Response Content documentation below
#        for keycard_json in data['list']:
#            keycard = KeyCard.objects.get(bluetooth = keycard_json['cardNumber'])
#            keycard.lock = obj
#            keycard.save()
#
#    return HttpResponse("OK")
#


#'''
#    EKeys
#'''
#@group_required("admins")
#def ekeys(request):
#    URL = "https://app.tullaveonline.com"
#    URL2 = "https://app.tullaveonline.com/?controller=login"
#    URL3 = "https://app.tullaveonline.com/?controller=precheckin"
#    client = requests.session()
#    page = client.get(URL)
#    login_data = dict(usuario="admin", password="admin", action="dologin")
#    r = client.post(URL2, data=login_data, headers=dict(Referer=URL))
#    page = client.get(URL3)
#    return render (request, "web/ekeys.html", {'page': page.text.replace('src="js/', 'src="https://app.millaveonline.com/js/')})
#

