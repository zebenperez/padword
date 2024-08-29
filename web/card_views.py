from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 
from django.views.decorators.csrf import csrf_exempt

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate, set_session, reverse_cardkey
from padword.decorators import group_required
from guest.models import KeyCard as GuestKeyCard
from .models import *
from .models_lock import *

from django.conf import settings
import os
import requests


def get_projects(request):
    search_value = request.session["keycard_search_name"] if "keycard_search_name" in request.session else ""
    projects = Project.objects.filter(name__icontains=search_value) if search_value != "" else Project.objects.all()
    return projects

@group_required("admins")
def keycards (request):
    return render (request, "web/keycards/keycards.html", {'project_list': get_projects(request), 'active': 'keycard'})
#    projects = Project.objects.all()
#    list_keycards = []
#    for project in projects:
#        list_keycards.append([project, KeyCard.objects.filter(project_uuid = project.uuid)])
#    return render (request, "web/keycards/keycards.html", {'list_keycards':list_keycards})

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
    return render (request, "web/keycards/keycards-list.html", {'project_list': get_projects(request)})
    #items = KeyCard.objects.filter(parent__isnull = True)
    #return render (request, "web/keycards/keycards-list.html",{'items':items} )

@group_required("admins")
def keycard_floors(request):
    project_uuid = request.GET["project"]
    project = Project.objects.get(uuid=project_uuid)
    return render(request, "web/keycards/keycards-list.html", {'project_list': [project]})
    #items = KeyCard.objects.filter(parent__isnull = True, project_uuid=project_uuid)
    #return render(request, "web/keycards/keycards-list.html", {'items': items,'project':project})

@group_required("admins")
def keycard_search (request):
    set_session(request, "keycard_search_name")
    return render (request, "web/keycards/keycards-list.html", {'project_list': get_projects(request)})


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

