from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, translate2, get_float
from web.models import Project
from contents.models import PointOfSale, PaymentType

from .models import Form, FormInstance, FormInstanceInfo, Cash
from .tpv_lib import get_cash, get_date_z, update_cash

import csv, datetime, logging, os, re
logger = logging.getLogger(__name__)


'''
    TPV Orders Daily
'''
def search(project_uuid, pos):
    kwargs = {'project_uuid': project_uuid}
    if pos != None:
        kwargs["pos_uuid"] = pos.uuid
    return Cash.objects.filter(**kwargs).order_by('-date')
 
@group_required("projects")
def cash_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        point_of_sales = PointOfSale.objects.filter(project_uuid=project.uuid)
        cash_list = Cash.objects.filter(project_uuid=project.uuid).order_by('-date')
        return render (request, "bookings/tpv-cash/index.html", {"pos_list": point_of_sales, 'cash_list': cash_list})
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-cash_by_project] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def cash_search(request):
    try:
        project = get_or_none(Project, request.project_id)
        pos_id = get_param(request.GET, "s-pos")
        pos = get_or_none(PointOfSale, pos_id)
        items = search(project.uuid, pos)

        return render(request, "bookings/tpv-cash/index-content.html", {'pos': pos, 'cash_list': items})
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def cash_new(request):
    try:
        project = get_or_none(Project, request.project_id)
        pos = get_or_none(PointOfSale, request.GET["obj_id"]) 
        ini_cash = get_float(request.GET["ini_cash"].replace(",", "."))

        items = search(project.uuid, pos)
        cash, created = get_cash(pos, get_date_z(), request.user.username)
        cash.ini_cash = ini_cash
        cash.save()
        return render(request, "bookings/tpv-cash/index-content.html", {'pos': pos, 'cash_list': items})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})


@group_required("projects")
def cash_remove(request):
    try:
        obj = get_or_none(Cash, request.GET["obj_id"]) 
        pos = obj.pos
        project_uuid = obj.project_uuid
        obj.delete()
        items = search(project_uuid, pos)

        return render(request, "bookings/tpv-cash/index-content.html", {'pos': pos, 'cash_list': items})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("projects")
def cash_z(request):
    try:
        project = get_or_none(Project, request.project_id)
        cash = get_or_none(Cash, request.GET["obj_id"]) 
        items = search(project.uuid, cash.pos)
        cash = update_cash(cash, request.user)
        cash.close = True
        cash.save()
        #cash = generate_cash(project, pos, request.user, date_str, cash_type, ini_cash)
        return render(request, "bookings/tpv-cash/index-content.html", {'pos': cash.pos, 'cash_list': items})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("projects")
def print_z(request, obj_id):
    try:
        cash = get_or_none(Cash, obj_id)
        return render(request, "bookings/tpv-cash/print-z.html", {'obj': cash,})
    except Exception as e:
        return HttpResponse("Error: {}".format(e))

