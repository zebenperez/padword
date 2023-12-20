from django.conf import settings
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, translate2, get_float
from web.models import Project
from contents.models import PointOfSale, PaymentType

from .models import Form, FormInstance, FormInstanceInfo

import csv, datetime, logging, os, re
logger = logging.getLogger(__name__)

FILES_DIR = os.path.join(settings.BASE_DIR, "media/tpv/orders-daily/")

'''
    TPV Orders Daily
'''
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
        file_list = [f for f in os.listdir(FILES_DIR)]
        return render (request, "bookings/tpv-orders-daily/index.html", {"pos_list": point_of_sales, 'file_list': file_list})
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

        file_list = [f for f in os.listdir(FILES_DIR) if re.match(r'.*{}*'.format(pos.regular_name), f)]
        return render(request, "bookings/tpv-orders-daily/index-content.html", {'pos': pos, 'file_list': file_list})
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def orders_daily_summary(request):
    try:
        obj = get_or_none(PointOfSale, request.GET["obj_id"]) 
        date_str = request.GET["date"]

        #response = HttpResponse(
        #    content_type='text/csv',
        #    headers={'Content-Disposition': 'attachment; filename="{}_{}.csv"'.format(date_str, obj.name)},
        #)

        f = open("{}{}_{}.csv".format(FILES_DIR, date_str, obj.regular_name), "w", encoding='utf-8')

        writer = csv.writer(f)
        writer.writerow(['_TPV', '_TPVNom', '_Rate', 'ProductUId', '_Description', 'Date', 'Tiket_UID', '_Price', '_Units', '_Discount', 'TotalPrice', '_Room', '_ClientId'])

        s_date = datetime.datetime.strptime("{} 00:00".format(date_str), "%Y-%m-%d %H:%M")
        e_date = datetime.datetime.strptime("{} 23:59:59".format(date_str), "%Y-%m-%d %H:%M:%S")
        fi_list = FormInstance.objects.filter(pos_uuid=obj.uuid, date__range=(s_date, e_date))
        for fi in fi_list:
            info = fi.info.first()
            room = info.client_room if info != None else ""
            client_id = info.client_id if info != None else ""
            for item in fi.get_items:
                code = obj.name[:4].upper()
                name = obj.name
                desc = translate2("es", item.name) 
                date = fi.date.strftime("%Y%m%d%H%M")
                discount = (item.low_price/item.price)*100 if item.low_price < item.price else 0
                total_price = item.low_price if item.low_price < item.price else item.price
                writer.writerow([code, name, "", item.id, desc, date, fi.id, item.price, 1, discount, total_price, room, client_id])

        file_list = [f for f in os.listdir(FILES_DIR) if re.match(r'.*{}*'.format(obj.regular_name), f)]
        return render(request, "bookings/tpv-orders-daily/index-content.html", {'pos': obj, 'file_list': file_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("projects")
def orders_daily_remove(request):
    try:
        obj = get_or_none(PointOfSale, request.GET["obj_id"]) 
        name = request.GET["name"]
        os.remove("{}{}".format(FILES_DIR, name))
        file_list = [f for f in os.listdir(FILES_DIR) if re.match(r'.*{}*'.format(obj.regular_name), f)]
        return render(request, "bookings/tpv-orders-daily/index-content.html", {'pos': obj, 'file_list': file_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("projects")
def orders_z(request):
    try:
        obj = get_or_none(PointOfSale, request.GET["obj_id"]) 
        date_str = request.GET["date"]

        s_date = datetime.datetime.strptime("{} 00:00".format(date_str), "%Y-%m-%d %H:%M")
        e_date = datetime.datetime.strptime("{} 23:59:59".format(date_str), "%Y-%m-%d %H:%M:%S")
        fi_list = FormInstance.objects.filter(pos_uuid=obj.uuid, date__range=(s_date, e_date))
        total = 0
        dic = {}
        pt_list = PaymentType.objects.all()
        for pt in pt_list:
            dic[translate2("es", pt.name)] = 0
        for fi in fi_list:
            #info = fi.info.first()
            #total += get_float(fi.amount)
            dic[translate2("es", fi.payment_type.name)] += get_float(fi.amount)
            print(fi.payment_type.name)
        print(dic)
        return render(request, "bookings/tpv-orders-daily/index-z.html", {'pos': obj, 'dic': dic})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})


