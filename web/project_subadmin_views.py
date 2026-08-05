from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, set_session, get_int
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
@group_required("project_subadmin")
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
        return render(request, "web/projects-subadmin/projects.html", {'items':items, 'company': company, 'active': 'projects'})
    except Exception as e:
        print (show_exc(e))
        company = None
        items = Project.objects.all()
        return render(request, "web/projects-subadmin/projects.html", {'items':items, 'company': company})

@group_required("project_subadmin")
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
        return render(request, "web/projects-subadmin/project-list.html", {'items': items, 'company_id': company_id,})
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_subadmin")
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
        return render(request, "web/projects-subadmin/project-details.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_subadmin")
def project_user_token(request):
    obj = get_or_none(ProjectLockUser, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.get_token()
    return render(request, "web/projects-subadmin/project-form-token.html", {'obj': obj.project, 'user_lock': obj,})


@group_required("project_subadmin")
def project_user_refresh_token(request):
    project = get_or_none(Project, get_param(request.GET, "obj_id"))
    user_lock = project.lock_user
    if user_lock != None:
        user_lock.get_new_token()
    return render(request, "web/projects-subadmin/project-form-token.html", {'obj': obj.project, 'user_lock': user_lock,})

@group_required("project_subadmin")
def locks_by_project(request, project_id):
    project = get_or_none(Project, project_id)
    try:
        lock_list = Lock.objects.filter(project_uuid=project.uuid)
        lg_list = LockGroup.objects.filter(project_uuid=project.uuid)
        context = {"project": project, "msg": "", "items": lock_list, "lock_group_list": lg_list}
        return render(request, "web/projects-subadmin/locks.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_subadmin")
def lock_update_params(request):
    lock = get_or_none(Lock, request.GET["obj_id"])
    lock.update_params()
    return render(request, "web/projects-subadmin/lock-list-row.html", {"item": lock})

@group_required("project_subadmin")
def lock_get_all_passcodes(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/projects-subadmin/lock-all-passcodes.html", {'obj': obj,})

@group_required("project_subadmin")
def lock_get_all_cards(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/projects-subadmin/lock-all-cards.html", {'obj': obj,})

@group_required("project_subadmin")
def lock_get_all_records(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/projects-subadmin/lock-all-records.html", {'obj': obj,})

@group_required("project_subadmin")
def lock_form(request):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/projects-subadmin/lock-form.html", {'obj': obj,})

@group_required("project_subadmin")
def gateways_by_project(request, project_id):
    try:
        project = get_or_none(Project, project_id)
        return render (request, "web/projects-subadmin/gateways.html", {'project': project, 'gateway_list': project.gateway_list()})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


