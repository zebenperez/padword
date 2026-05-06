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
@group_required("project_manager")
def projects(request):
    try:
        items = Project.objects.filter(manager=request.user)
        return render(request, "web/projects-manager/projects.html", {'items':items, 'active': 'projects'})
    except Exception as e:
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
        if "obj_id" in request.GET:
            obj = get_or_none(Project, request.GET["obj_id"])  
        else: 
            comp = Company.objects.filter(active=1).first()
            obj = Project.objects.create(company=comp, manager=request.user, uuid=new_ui_slug(Project))

        #aux = get_or_create_projectaux(obj)
        #user_lock = get_or_create_user_lock(obj.uuid)
        #user_sensibo = get_or_create_user_sensibo(obj.uuid)
        #user_avantio = get_or_create_user_avantio(obj.uuid)
        #user_avaibook = get_or_create_user_avaibook(obj.uuid)
        #user_winhotel = get_or_create_user_winhotel(obj.uuid)
        #user_stripe = get_or_create_user_stripe(obj.uuid)
        #user_mews = get_or_create_user_mews(obj.uuid)
        #user_cloudbeds = get_or_create_user_cloudbeds(obj.uuid)
        #user_cars = get_or_create_user_cars(obj.uuid)
        #user_paytef = get_or_create_user_paytef(obj.uuid)
        #user_zkteco = get_or_create_user_zkteco(obj.uuid)
        #user_roomraccoon = get_or_create_user_roomraccoon(obj.uuid)
        #user_octorate = get_or_create_user_octorate(obj.uuid)

        #regime_list = Regime.objects.filter(project_uuid="")
        #point_of_sale_list = PointOfSale.objects.filter(project_uuid=obj.uuid)
        #form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=obj.uuid).first()
        context = {
            'obj': obj, 
            #'aux': aux, 
            'companies': Company.objects.all(), 
            #'company_id': company_id, 
            #'user_lock': user_lock, 
            #'user_sensibo': user_sensibo, 
            #'user_avantio': user_avantio, 
            #'user_avaibook': user_avaibook, 
            #'user_winhotel': user_winhotel, 
            #'user_stripe': user_stripe, 
            #'user_mews': user_mews, 
            #'user_cloudbeds': user_cloudbeds, 
            #'user_cars': user_cars, 
            #'user_paytef': user_paytef, 
            #'user_zkteco': user_zkteco, 
            #'user_roomraccoon': user_roomraccoon, 
            #'user_octorate': user_octorate, 
            #'project_regime_list': [item.regime for item in obj.regimes.all()],
            #'regime_list': regime_list,
            #'point_of_sale_list': point_of_sale_list,
            #'form': form
        }
        return render(request, "web/projects-manager/project-form.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


#@group_required("project_admin")
#def project_user_refresh_token(request):
#    project = get_or_none(Project, get_param(request.GET, "obj_id"))
#    user_lock = project.lock_user
#    if user_lock != None:
#        user_lock.get_new_token()
#    return render(request, "web/projects-admin/project-form-token.html", {'obj': project, 'user_lock': user_lock,})
#

