from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, set_session, get_int
from padword.decorators import group_required
from padword.email_lib import send_email
from .models import *
from .models_lock import *
from contents.models import Category
from bookings.models import Form, FormType

from django.conf import settings
import os, re, requests, time, datetime, csv


def get_or_create_projectaux(project):
    obj, created = ProjectAux.objects.get_or_create(project = project)
    return obj 

'''
    Projects
'''
@group_required("project_manager")
def projects(request):
    try:
        items = Project.objects.filter(manager=request.user)
        return render(request, "web/projects-manager/projects.html", {'items':items, 'active': 'projects'})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_manager")
def projects_search(request):
    try:
        name = get_param(request.GET, "s-name")
        kwargs = {'manager': request.user}
        if name != "":
            kwargs["name_icontains"] = name
        items = Project.objects.filter(**kwargs)
        return render(request, "web/projects-manager/project-list.html", {'items': items,})
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_manager")
def projects_details(request, obj_id, current_tab=""):
    try:
        obj = get_or_none(Project, obj_id) 
        if obj.manager != request.user:
            return render(request, 'error_exception.html', {'exc': 'Permission denied!'})

        aux = get_or_create_projectaux(obj)
        context = {
            'obj': obj, 
            'aux': aux, 
            'companies': Company.objects.all(), 
            'thirdpart_list': Thirdpart.objects.all(), 
            'user_lock': ProjectLockUser.objects.filter(project_uuid = obj.uuid).first()
        }
        return render(request, "web/projects-manager/project-details.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_manager")
def projects_form(request):
    try:
        #obj = get_or_none(Project, get_param(request.GET, "obj_id"))  
        #context = { 'obj': obj, 'companies': Company.objects.all(), 'uuid': new_ui_slug(Project) }
        context = { 'obj': None, 'companies': Company.objects.all(), 'uuid': new_ui_slug(Project) }
        return render(request, "web/projects-manager/project-form.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_manager")
def project_user_token(request):
    obj = get_or_none(ProjectLockUser, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj.project.manager != request.user:
        return render(request, 'error_exception.html', {'exc': 'Permission denied!'})
    if obj != None:
        obj.get_token()
    return render(request, "web/projects-manager/project-token.html", {'user_lock':obj,})

@group_required("project_manager")
def project_user_refresh_token(request):
    project = get_or_none(Project, get_param(request.GET, "obj_id"))
    if project.manager != request.user:
        return render(request, 'error_exception.html', {'exc': 'Permission denied!'})
    user_lock = project.lock_user
    if user_lock != None:
        user_lock.get_new_token()
    return render(request, "web/projects-manager/project-form-token.html", {'obj': project, 'user_lock': user_lock,})

@group_required("project_manager")
def categories_by_project(request, project_id):
    project = Project.objects.get(uuid=project_id)
    cat = Category.objects.filter(project_uuid=project_id, parent__isnull=True).first()
    if cat == None:
        cat = Category.objects.create(
                project_uuid=project_id, 
                name=project.name, 
                uuid=new_ui_slug(Category),
                created_at=datetime.datetime.now(),
                is_active=1,
                updated_at=datetime.datetime.now()
        )
        emails = ["davidhdez@shidix.com", "zebenperez@shidix.com", "zebenperez@gmail.com", "a.serrano@padword.es"]
        send_email("Nueva PWA", f'Se ha creado una nueva PWA en el proyecto {project.name}', "no-reply@padword.com", emails)
    ft = FormType.objects.filter(name=cat.name, project_uuid=project.uuid).first()
    if ft == None:
        ft = FormType.objects.create(
                code = f'menu_{project.name[:5].lower()}', 
                name = cat.name, 
                template = "bookings/menus/menu_keys.html",
                template_base = "bookings/menus/menu_keys_base.html",
                template_login = "bookings/login/login_languages.html",
                project_uuid = project.uuid)
    f = Form.objects.filter(category=cat).first()
    if f == None:
        f = Form.objects.create(category=cat, form_type=ft, uuid=new_ui_slug(Form))
    return render(request, "web/projects-manager/categories.html", {'project':project, 'item':cat})

'''
    Companies
'''
@group_required("project_manager")
def companies(request):
    try:
        items = Company.objects.filter(manager=request.user)
        return render (request, "web/projects-manager/companies.html",{'items':items, 'active': 'companies'} )
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_manager")
def companies_search(request):
    try:
        name = get_param(request.GET, "s-name")
        kwargs = {'manager': request.user}
        if name != "":
            kwargs["name_icontains"] = name
        items = Company.objects.filter(**kwargs)
        return render(request, "web/projects-manager/companies-list.html", {'items': items,})
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_manager")
def companies_form(request):
    obj = get_or_none(Company, get_param(request.GET, "obj_id")) 
    uuid = obj.uuid if obj != None else new_ui_slug(Company)
    return render(request, "web/projects-manager/companies-form.html", {'obj': obj, 'uuid': uuid})

'''
    Rooms
'''
@group_required("project_manager")
def rooms(request, project_uuid):
    try:
        project = get_or_none(Project, project_uuid, "uuid")
        group_list = LockGroup.objects.filter(project_uuid=project.uuid)
        return render (request, "web/projects-manager/rooms.html",{'project': project, 'group_list': group_list} )
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("project_manager")
def rooms_search (request):
    name = get_param(request.GET, "room_search_name")
    project = get_or_none(Project, get_param(request.GET, "project_uuid"), "uuid")
    group_list = LockGroup.objects.filter(project_uuid=project.uuid)
    return render (request, "web/rooms/rooms-list.html", {'project': project, "search_name":name})

@group_required("project_manager")
def rooms_form(request):
    print("--1--")
    try:
        project_uuid = get_param(request.GET, "project")

        obj = get_or_none(Room, get_param(request.GET, "obj_id")) 
        uuid = obj.uuid if obj != None else new_ui_slug(Room)
        group_list = LockGroup.objects.filter(project_uuid = project_uuid)
        print("--2--")
        context = {'project': project, 'obj':obj, 'uuid':uuid, 'group_list':group_list}
        return render(request, "web/projects-manager/rooms-form.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

