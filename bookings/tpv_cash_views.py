from django.conf import settings
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, translate2, get_float
from web.models import Project
from contents.models import PointOfSale, PaymentType

from .models import Form, FormInstance, FormInstanceInfo, Cash

import csv, datetime, logging, os, re
logger = logging.getLogger(__name__)


'''
    TPV Orders Daily
'''
def search(project_uuid, pos):
    kwargs = {'project_uuid': project_uuid}
    if pos != None:
        kwargs["pos_uuid"] = pos.uuid
    return Cash.objects.filter(**kwargs)
 
@group_required("projects")
def cash_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        point_of_sales = PointOfSale.objects.filter(project_uuid=project.uuid)
        cash_list = Cash.objects.filter(project_uuid=project.uuid)
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
        pos = get_or_none(PointOfSale, request.GET["obj_id"]) 
        date_str = request.GET["date"]
        ini_cash = get_float(request.GET["ini_cash"].replace(",", "."))

        s_date = datetime.datetime.strptime("{} 00:00".format(date_str), "%Y-%m-%d %H:%M")
        e_date = datetime.datetime.strptime("{} 23:59:59".format(date_str), "%Y-%m-%d %H:%M:%S")
        fi_list = FormInstance.objects.filter(pos_uuid=pos.uuid, date__range=(s_date, e_date))

        cash_total = 0
        band_total = 0
        card_total = 0
        return_total = 0
        free_total = 0
        for fi in fi_list:
            print(fi.get_status)
            if fi.get_status == None:
                fi.set_status("05", request.user, "Cancell in Z!")
            elif fi.get_status.status != None and fi.get_status.status.code != "05":
                amount = get_float(fi.amount.replace(",", "."))
                if fi.payment_type.code == "01":
                    cash_total += amount
                elif fi.payment_type.code == "02":
                    card_total += amount
                elif fi.payment_type.code == "03":
                    band_total += amount
                elif fi.payment_type.code == "04":
                    return_total += amount
                elif fi.payment_type.code == "05":
                    free_total += amount

        cash = Cash(project_uuid = project.uuid, pos_uuid = pos.uuid)
        cash.date = e_date
        cash.ini_cash = ini_cash
        cash.end_cash = cash_total
        cash.band = band_total
        cash.card = card_total
        cash.username = request.user.username
        cash.save()

        items = search(project.uuid, pos)
        return render(request, "bookings/tpv-cash/index-content.html", {'pos': pos, 'cash_list': items})
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

