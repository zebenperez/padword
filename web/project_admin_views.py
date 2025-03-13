from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, set_session, get_int
from padword.decorators import group_required
from .models import *

from django.conf import settings
import os, re, requests, time, datetime, csv


def get_or_create_projectaux(project):
    obj, created = ProjectAux.objects.get_or_create(project = project)
    return obj 

'''
    Projects
'''
@group_required("project_admin")
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
        return render(request, "web/projects-admin/projects.html", {'items':items, 'company': company, 'active': 'projects'})
    except Exception as e:
        print (show_exc(e))
        company = None
        items = Project.objects.all()
        return render(request, "web/projects-admin/projects.html", {'items':items, 'company': company})

@group_required("project_admin")
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
        return render(request, "web/projects-admin/project-list.html", {'items': items, 'company_id': company_id,})
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_admin")
def projects_details(request, obj_id, current_tab=""):
    try:
        obj = get_or_none(Project, obj_id) 
        aux = get_or_create_projectaux(obj)
        context = { 'obj': obj, 'aux': aux, 'companies': Company.objects.all(), 'thirdpart_list': Thirdpart.objects.all()}
        return render(request, "web/projects-admin/project-details.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


