from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, set_session, get_int, reverse_cardkey
from padword.decorators import group_required
from .models import *
from .models_lock import Lock, LockGroup

from django.conf import settings
import os, re, requests, time, datetime, csv


def get_or_create_projectaux(project):
    obj, created = ProjectAux.objects.get_or_create(project = project)
    return obj 

'''
    Projects
'''
@group_required("project_satadmin")
def projects(request, company_id=None, project_id=None):
    try:
        company = None
        if project_id is not None:
            project = get_or_none(Project, project_id, 'uuid')
            items = Project.objects.all() if project is None else Project.objects.filter(uuid = project.uuid)
        elif company_id is not None:
            company = get_or_none(Company, company_id)
            items = Project.objects.all() if company is None else Project.objects.filter(company = company)
        else:
            items = Project.objects.all()
        return render(request, "web/projects-satadmin/projects.html", {'items':items, 'company': company, 'active': 'projects'})
    except Exception as e:
        print (show_exc(e))
        company = None
        items = Project.objects.all()
        return render(request, "web/projects-satadmin/projects.html", {'items':items, 'company': company})

@group_required("project_satadmin")
def projects_search(request):
    try:
        company_id = get_param(request.GET, "company_id")
        name = get_param(request.GET, "s-name")
        filters_to_search = ["name__icontains", "company__name__icontains"]
        items = Channel.objects.none()
        for myfilter in filters_to_search:
            kwargs = {}
            if company_id != "":
                kwargs["company__id"] = company_id
            if name != "":
                kwargs[myfilter] = name
            items = items.union(Project.objects.filter(**kwargs))
        return render(request, "web/projects-satadmin/project-list.html", {'items': items, 'company_id': company_id,})
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_satadmin")
def projects_details(request, obj_id, current_tab=""):
    try:
        obj = get_or_none(Project, obj_id) 
        aux = get_or_create_projectaux(obj)
        context = {
            'obj': obj, 
            'aux': aux, 
            'companies': Company.objects.all(), 
            'thirdpart_list': Thirdpart.objects.all(), 
            'user_lock': ProjectLockUser.objects.filter(project_uuid = obj.uuid).first()
        }
        return render(request, "web/projects-satadmin/project-details.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

#@group_required("project_satadmin")
#def project_user_token(request):
#    obj = get_or_none(ProjectLockUser, request.GET["obj_id"]) if "obj_id" in request.GET else None
#    if obj != None:
#        obj.get_token()
#    return render(request, "web/projects-satadmin/project-form-token.html", {'obj': project, 'user_lock': user_lock,})

@group_required("project_satadmin")
def project_user_refresh_token(request):
    project = get_or_none(Project, get_param(request.GET, "obj_id"))
    user_lock = project.lock_user
    if user_lock != None:
        user_lock.get_new_token()
    return render(request, "web/projects-satadmin/project-form-token.html", {'obj': project, 'user_lock': user_lock,})

@group_required("project_satadmin")
def locks_by_project(request, project_id):
    project = get_or_none(Project, project_id)
    try:
        lock_list = Lock.objects.filter(project_uuid=project.uuid)
        alias = get_param(request.GET, "lock_search_alias")
        passcode = get_param(request.GET, "lock_search_passcode")
        cardcode = get_param(request.GET, "lock_search_cardcode")
        group_name = get_param(request.GET, "lock_search_group")
        if alias:
            lock_list = lock_list.filter(alias__icontains=alias)
        if group_name:
            group_uuids = LockGroup.objects.filter(
                project_uuid=project.uuid,
                name__icontains=group_name,
            ).values_list("uuid", flat=True)
            lock_list = lock_list.filter(group_uuid__in=group_uuids)
        lock_list = list(lock_list)
        if passcode:
            lock_list = [lock for lock in lock_list if passcode in lock.code_cache]
        if cardcode:
            card_number = str(reverse_cardkey(cardcode))
            lock_list = [lock for lock in lock_list if card_number in lock.card_cache]
        lg_list = LockGroup.objects.filter(project_uuid=project.uuid)
        context = {
            "project": project,
            "msg": "",
            "items": lock_list,
            "lock_group_list": lg_list,
            "lock_search_alias": alias,
            "lock_search_passcode": passcode,
            "lock_search_cardcode": cardcode,
            "lock_search_group": group_name,
        }
        return render(request, "web/projects-satadmin/locks.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_satadmin")
def lock_set_group(request):
    project = get_or_none(Project, get_param(request.POST, "project_uuid"), "uuid")
    group_uuid = get_param(request.POST, "lock_group")

    if project is None:
        return render(request, 'error_exception.html', {'exc': 'Project not found!'})

    group = None
    if group_uuid:
        group = LockGroup.objects.filter(uuid=group_uuid, project_uuid=project.uuid).first()
    if group_uuid and group is None:
        return render(request, 'error_exception.html', {'exc': 'Lock group not found!'})

    lock_ids = [key.removeprefix("ch_") for key in request.POST if key.startswith("ch_")]
    locks = Lock.objects.filter(id__in=lock_ids, project_uuid=project.uuid)
    for lock in locks:
        lock.group_uuid = group.uuid if group else ""
        lock.save()
        lock.set_group()

    return redirect('projects-satadmin-locks-by-project', project_id=project.id)

@group_required("project_satadmin")
def lock_update_params(request):
    lock = get_or_none(Lock, request.GET["obj_id"])
    lock.update_params()
    return render(request, "web/projects-satadmin/lock-list-row.html", {"item": lock})

@group_required("project_satadmin")
def lock_get_all_passcodes(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/projects-satadmin/lock-all-passcodes.html", {'obj': obj,})

@group_required("project_satadmin")
def lock_get_all_cards(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/projects-satadmin/lock-all-cards.html", {'obj': obj,})

@group_required("project_satadmin")
def lock_get_all_records(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/projects-satadmin/lock-all-records.html", {'obj': obj,})

@group_required("project_satadmin")
def lock_form(request):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/projects-satadmin/lock-form.html", {'obj': obj,})

@group_required("project_satadmin")
def gateways_by_project(request, project_id):
    try:
        project = get_or_none(Project, project_id)
        return render (request, "web/projects-satadmin/gateways.html", {'project': project, 'gateway_list': project.gateway_list()})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})
