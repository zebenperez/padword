from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 
from django.views.decorators.csrf import csrf_exempt
import datetime

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate, set_session, reverse_cardkey, get_int
from padword.decorators import group_required
from guest.models import KeyCard as GuestKeyCard
from .models import *
from .models_lock import *

from django.conf import settings
import os
import requests


def get_context(project_uuid):
    project = get_or_none(Project, project_uuid, "uuid")
    item_list = KeyCard.objects.filter(project_uuid=project.uuid)
    return {'project': project, 'item_list': item_list, 'active': 'keycard'}

@group_required("admins")
def keycards_by_project (request, project_uuid):
    return render (request, "web/keycards/keycards.html", get_context(project_uuid))

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
    project_uuid = get_param(request.GET, "project")
    if obj != None:
        obj.delete()
    return render (request, "web/keycards/keycards-list.html", get_context(project_uuid))

@group_required("admins")
def keycard_search (request):
    set_session(request, "keycard_search_name")
    return render (request, "web/keycards/keycards-list.html", {'project_list': get_projects(request)})

'''
    Keycard multiple
'''
@group_required("admins")
def keycards_add_multiple (request, project_uuid):
    project = get_or_none(Project, project_uuid, "uuid")
    #items = Lock.objects.filter(project_uuid=project.uuid)
    now = datetime.datetime.now()
    context = {"project": project, "ini_date": now.strftime("%Y-%m-%d"), "end_date": now.strftime("%Y-%m-%d")}
    #context = {"project": project, "items": items, "ini_date": now.strftime("%Y-%m-%d"), "end_date": now.strftime("%Y-%m-%d")}
    return render (request, "web/keycards/keycards-add-multiple.html", context)

@group_required("projects")
def keycards_add_multiple_by_project(request, group=""):
    project = get_or_none(Project, request.project_id)
    now = datetime.datetime.now()
    context = {"project": project, "ini_date": now.strftime("%Y-%m-%d"), "end_date": now.strftime("%Y-%m-%d"), "group": str(group)}
    return render (request, "web/keycards/keycards-add-multiple.html", context)

@group_required("projects")
def keycode_add_multiple_by_project(request, group=""):
    project = get_or_none(Project, request.project_id)
    now = datetime.datetime.now()
    context = {
        "project": project, 
        "ini_date": now.strftime("%Y-%m-%d"), 
        "end_date": now.strftime("%Y-%m-%d"), 
        "group": str(group),
        "code": "True"
    }
    return render (request, "web/keycards/keycards-add-multiple.html", context)

@group_required("admins", "projects")
def keycards_add_multiple_step1(request):
    project = get_or_none(Project, get_param(request.POST, "project"), "uuid")
    number = get_int(get_param(request.POST, "number"))
    ini_date = get_param(request.POST, "ini_date")
    end_date = get_param(request.POST, "end_date")
    group = get_param(request.POST, "group")
    code = get_param(request.POST, "code")
    #items = Lock.objects.filter(project_uuid=project.uuid, default=True)
    items = Lock.objects.filter(project_uuid=project.uuid)
    context = {
        "project": project, 
        "number": number, 
        "ini_date": ini_date, 
        "end_date": end_date, 
        "items": items, 
        "group": group, 
        "code": code
    }
    return render (request, "web/keycards/keycards-add-multiple-step1.html", context)
 
@group_required("admins", "projects")
def keycards_add_multiple_step2(request):
    project = get_or_none(Project, get_param(request.POST, "project"), "uuid")
    number = get_int(get_param(request.POST, "number"))
    ini_date = get_param(request.POST, "ini_date")
    end_date = get_param(request.POST, "end_date")
    group = get_param(request.POST, "group")
    code = get_param(request.POST, "code")
    locks = ""
    items = []
    for key in request.POST.keys():
        if key.startswith("ch_"):
            #val = get_int(key.split("_")[1])
            val = get_int(get_param(request.POST, key))
            if val > 0:
                locks += "{},".format(val)
                items.append(get_or_none(Lock, val))
    context = {
        "project": project, 
        "number" :number, 
        "range": range(number), 
        "locks": locks[:-1], 
        "ini_date": ini_date, 
        "end_date": end_date, 
        "group": group, 
        "code": code, 
        "items": items
    }
    return render (request, "web/keycards/keycards-add-multiple-step2.html", context)
 
@group_required("admins", "projects")
def keycards_add_multiple_step3(request):
    project = get_or_none(Project, get_param(request.POST, "project"), "uuid")
    locks = get_param(request.POST, "locks")
    ini_date= "{} 00:00:00".format(get_param(request.POST, "ini_date"))
    end_date= "{} 23:59:59".format(get_param(request.POST, "end_date"))
    name = get_param(request.POST, "name")
    group = get_param(request.POST, "group")
    code = get_param(request.POST, "code")
    card = get_param(request.POST, "card")
    #card = reverse_cardkey(get_param(request.POST, "card"))
    current = get_int(get_param(request.POST, "current"))
    total = get_int(get_param(request.POST, "total"))
    percent = (current * 100) // total
    lock_list = locks.split(",")
    err = ""
    for lock in lock_list:
        l = get_or_none(Lock, lock)
        i_date = datetime.datetime.strptime(ini_date, "%Y-%m-%d %H:%M:%S")
        e_date = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        #print("{} {} {} {}".format(card, ini_date, end_date, name))
        if code == "True":
            err = l.add_card(reverse_cardkey(card), i_date, e_date, name)
        else:
            err = l.set_code(card, i_date, e_date, name)
    context = {"percent": percent, "project_uuid": project.uuid, "group": group, "err": err}
    return render (request, "web/keycards/keycards-add-multiple-progress.html", context)

@group_required("admins", "projects")
def keycards_add_multiple_locks(request):
    project = get_or_none(Project, get_param(request.GET, "obj_id"), "uuid")
    items = Lock.objects.filter(project_uuid=project.uuid, default=False)
    return render (request, "web/keycards/keycards-add-multiple-locks.html", {"items": items})
 
@group_required("admins", "projects")
def keycards_add_multiple_locks_select(request):
    #project = get_or_none(Project, get_param(request.POST, "project"), "uuid")
    locks = ""
    items = []
    for key in request.POST.keys():
        if key.startswith("ch_"):
            val = get_int(get_param(request.POST, key))
            if val > 0:
                locks += "{},".format(val)
                items.append(get_or_none(Lock, val))
    return render (request, "web/keycards/keycards-add-multiple-locks-select.html", {"locks": locks[:-1], "items": items})
 
#def get_projects(request):
#    search_value = request.session["keycard_search_name"] if "keycard_search_name" in request.session else ""
#    projects = Project.objects.filter(name__icontains=search_value) if search_value != "" else Project.objects.all()
#    return projects
#
#@group_required("admins")
#def keycards (request):
#    return render (request, "web/keycards/keycards.html", {'project_list': get_projects(request), 'active': 'keycard'})
#    projects = Project.objects.all()
#    list_keycards = []
#    for project in projects:
#        list_keycards.append([project, KeyCard.objects.filter(project_uuid = project.uuid)])
#    return render (request, "web/keycards/keycards.html", {'list_keycards':list_keycards})

#@group_required("admins")
#def keycard_floors(request):
#    project_uuid = request.GET["project"]
#    project = Project.objects.get(uuid=project_uuid)
#    return render(request, "web/keycards/keycards-list.html", {'project_list': [project]})


#@group_required("admins")
#def keycard_search(request):
#    try:
#        filters_to_search = ["alias__icontains", ]
#        items = KeyCard.objects.none()
#        for myfilter in filters_to_search:
#            kwargs = {}
#            if "s-alias" in request.GET and request.GET["s-alias"] != "":
#                kwargs[myfilter] = request.GET["s-alias"]
#            items = items.union(KeyCard.objects.filter(**kwargs))
#        return render(request, "web/keycards/keycards-list.html", {'items': items,})
#    except Exception as e:
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})


'''
    Key Number
'''
def number_search(value):
    card_result = []
    if value != "":
        cardkey = str(reverse_cardkey(value))
        lock_list = Lock.objects.all()
        for lock in lock_list:
            try:
                card_list = lock.get_all_cards()
                for card in card_list:
                    if (card["cardNumber"] == cardkey):
                        guest_card_list = GuestKeyCard.objects.filter(lock=lock, code=cardkey)
                        guests = ["{} {}".format(item.guest.name, item.guest.surname) for item in guest_card_list]
                        dic = {
                            'value': value, 
                            'project': lock.project.name, 
                            'lock_id': lock.id, 
                            'lock_alias': lock.alias, 
                            'lock_room': lock.room, 
                            'card_id': card["cardId"], 
                            'card_number': card["cardNumber"],
                            'card_name': card["cardName"],
                            'start_date': card["startDate"],
                            'end_date': card["endDate"],
                            'guests': "<br/>".join(guests)
                        }
                        card_result.append(dic)
            except Exception as e:
                #print(e)
                pass
    return card_result

@group_required("admins")
def keycard_number(request):
    return render (request, "web/keycards/keycard-number.html", {'active': 'searchkeycard'})

@group_required("admins")
def keycard_number_search(request):
    value = get_param(request.GET, "value")
    card_result = number_search(value)
    return render (request, "web/keycards/keycard-number-search.html", {'card_list': card_result})

@group_required("admins")
def keycard_number_guest_remove(request):
    value = request.GET["value"]
    card_id = request.GET["card_id"]
    lock_id = request.GET["lock"]
    card = get_param(request.GET, "card")

    lock = get_or_none(Lock, lock_id)
    lock.remove_card(card_id, card)
    card_result = number_search(value)
    return render (request, "web/keycards/keycard-number-search.html", {'card_list': card_result})

'''
    Key Number by project
'''
def number_search_by_project(value, project):
    card_result = []
    if value != "":
        cardkey = str(reverse_cardkey(value))
        lock_list = Lock.objects.filter(project_uuid = project.uuid)
        for lock in lock_list:
            try:
                if cardkey in lock.card_cache:
                    card_list = lock.get_all_cards()
                    for card in card_list:
                        if (card["cardNumber"] == cardkey):
                            guest_card_list = GuestKeyCard.objects.filter(lock=lock, code=cardkey)
                            guests = ["{} {}".format(item.guest.name, item.guest.surname) for item in guest_card_list]
                            dic = {
                                'value': value, 
                                'project': lock.project.name, 
                                'lock_id': lock.id, 
                                'lock_alias': lock.alias, 
                                'lock_room': lock.room, 
                                'card_id': card["cardId"], 
                                'card_number': card["cardNumber"],
                                'card_name': card["cardName"],
                                'start_date': card["startDate"],
                                'end_date': card["endDate"],
                                'guests': "<br/>".join(guests)
                            }
                            card_result.append(dic)
            except Exception as e:
                #print(e)
                pass
    return card_result

@group_required("projects")
def keycard_number_by_project(request):
    return render (request, "web/keycards-by-project/keycard-number.html", {'active': 'keycard'})

@group_required("projects")
def keycard_number_search_by_project(request):
    project = get_or_none(Project, request.project_id)
    value = get_param(request.GET, "value")
    card_result = number_search_by_project(value, project)
    return render (request, "web/keycards-by-project/keycard-number-search.html", {'card_list': card_result})

@group_required("projects")
def keycard_number_guest_remove_by_project(request):
    project = get_or_none(Project, request.project_id)
    value = request.GET["value"]
    card_id = request.GET["card_id"]
    lock_id = request.GET["lock"]
    card = get_param(request.GET, "card")

    lock = get_or_none(Lock, lock_id)
    lock.remove_card(card_id, card)
    card_result = number_search_by_project(value, project)
    return render(request, "web/keycards-by-project/keycard-number-search.html", {'card_list': card_result})

