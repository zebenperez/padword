from django.conf import settings
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, translate2, get_float
from web.models import Project
from contents.models import PointOfSale, PaymentType

from .models import Form, FormInstance, FormInstanceInfo
from .tpv_winhotel_lib import cash_daily_summary  

import csv, datetime, logging, os, re
logger = logging.getLogger(__name__)

FILES_DIR = os.path.join(settings.BASE_DIR, "media/tpv/orders-daily/")

'''
    TPV Orders Daily
'''
def getFiles(project_uuid, ext_code=""):
    path = "{}{}/".format(FILES_DIR, project_uuid)
    file_list = []
    if os.path.exists(path):
        if ext_code != "":
            file_list = [f for f in os.listdir(path) if re.match(r'.*{}*'.format(ext_code), f)]
        else:
            file_list = [f for f in os.listdir(path)]
        file_list.sort(key=str.lower, reverse=True)
    return file_list

def search(project_uuid, pos):
    form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=project_uuid).first()
    kwargs = {'form_uuid': form.uuid}
    if pos != None:
        kwargs["pos_uuid"] = pos.uuid
    return FormInstance.objects.filter(**kwargs)
 
@group_required("projects")
def orders_daily_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        point_of_sales = PointOfSale.objects.filter(project_uuid=project.uuid)
        file_list = getFiles(project.uuid)
        context = {"pos_list": point_of_sales, 'file_list': file_list, "project_uuid": project.uuid}
        return render (request, "bookings/tpv-orders-daily/index.html", context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-orders_by_project] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def orders_daily_search(request):
    try:
        project = get_or_none(Project, request.project_id)
        pos_id = get_param(request.GET, "s-pos")
        pos = get_or_none(PointOfSale, pos_id)
        items = search(project.uuid, pos)

        file_list = getFiles(project.uuid, pos.ext_code) if pos != None else getFiles(project.uuid)
        #file_list = [f for f in os.listdir("{}{}/".format(FILES_DIR, project.uuid)) if re.match(r'.*{}*'.format(pos.ext_code), f)]
        context = {'pos': pos, 'file_list': file_list, "project_uuid": project.uuid}
        return render(request, "bookings/tpv-orders-daily/index-content.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def orders_daily_summary(request):
    try:
        obj = get_or_none(PointOfSale, request.GET["obj_id"]) 
        date_str = request.GET["date"]
        cash_daily_summary(obj, date_str)
        file_list = getFiles(obj.project_uuid, obj.ext_code)
        context = {'pos': obj, 'file_list': file_list, "project_uuid": obj.project.uuid}
        return render(request, "bookings/tpv-orders-daily/index-content.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("projects")
def orders_daily_remove(request):
    try:
        obj = get_or_none(PointOfSale, request.GET["obj_id"]) 
        name = request.GET["name"]
        os.remove("{}{}/{}".format(FILES_DIR, obj.project_uuid, name))
        file_list = getFiles(obj.project_uuid, obj.ext_code)
        #file_list = [f for f in os.listdir("{}{}/".format(FILES_DIR, obj.project_uuid)) if re.match(r'.*{}*'.format(obj.ext_code), f)]
        context = {'pos': obj, 'file_list': file_list, "project_uuid": obj.project.uuid}
        return render(request, "bookings/tpv-orders-daily/index-content.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

#@group_required("projects")
#def orders_z(request):
#    try:
#        obj = get_or_none(PointOfSale, request.GET["obj_id"]) 
#        date_str = request.GET["date"]
#
#        s_date = datetime.datetime.strptime("{} 00:00".format(date_str), "%Y-%m-%d %H:%M")
#        e_date = datetime.datetime.strptime("{} 23:59:59".format(date_str), "%Y-%m-%d %H:%M:%S")
#        fi_list = FormInstance.objects.filter(pos_uuid=obj.uuid, date__range=(s_date, e_date))
#        total = 0
#        dic = {}
#        pt_list = PaymentType.objects.all()
#        for pt in pt_list:
#            dic[translate2("es", pt.name)] = 0
#        for fi in fi_list:
#            #info = fi.info.first()
#            #total += get_float(fi.amount)
#            dic[translate2("es", fi.payment_type.name)] += get_float(fi.amount)
#            print(fi.payment_type.name)
#        print(dic)
#        return render(request, "bookings/tpv-orders-daily/index-z.html", {'pos': obj, 'dic': dic})
#    except Exception as e:
#        print(e)
#        return render(request, 'error_exception.html', {'msg': str(e)})
#
#
