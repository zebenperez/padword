from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, get_bool, new_ui_slug, get_items_per_page
from web.models import Project
from contents.models import Category
from guest.models import Guest

from .models import Form, FormInstance, FormInstanceInfo, Status

import datetime
import logging
logger = logging.getLogger(__name__)

ITEMS_PER_PAGE=get_items_per_page()


'''
    Project users
'''
def filter_search_guest(name, uuid_project_list):
    uuid_guests = list(Guest.objects.filter(Q(name__icontains=name) | Q(surname__icontains=name) | Q(email__icontains=name) | Q(mobile__icontains=name) | Q(room=name)).filter(project_id__in = uuid_project_list).values_list('UUID', flat=True))
    return uuid_guests


def search(project_uuid, ini_date, end_date, name, status, s_id=""):
    if s_id != "":
        try:
            return FormInstance.objects.filter(id=s_id)
        except Exception as e:
            print(e)

    form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=project_uuid).first()

    kwargs = {'form_uuid': form.uuid}
    if ini_date != "":
        kwargs["date__gte"] = ini_date
    if end_date != "":
        ed = end_date.split("-")
        kwargs["date__lte"] = datetime.datetime(int(ed[0]), int(ed[1]), int(ed[2]), 23, 59, 59)
    if name != "":
        kwargs["guest_uuid__in"] = filter_search_guest(name, [project_uuid])

    return FormInstance.objects.filter(**kwargs)
    #items = FormInstance.objects.filter(**kwargs)
    #return filter_search_status_project(items, status, project_uuid)

def get_orders_project_context(project):
    context = {}
    today = datetime.datetime.today()
    ini_date = today + datetime.timedelta(days=-3)
    end_date = today + datetime.timedelta(days=1)
            
    items = search(project.uuid, ini_date, end_date.strftime("%Y-%m-%d"), "", "")

    context["project_uuid"] = project.uuid
    context["project_name"] = project.name
    context["ini_date"] = ini_date
    context["end_date"] = end_date
    context["status_list"] = Status.objects.all()
    context['items'] = items[0:ITEMS_PER_PAGE]
    context['total_items'] = len(items)
    return context

@group_required("projects")
def orders_search(request):
    try:
        project = get_or_none(Project, request.project_id)
        s_id = get_param(request.GET, "s-id")
        ini_date = get_param(request.GET, "s-ini_date")
        end_date = get_param(request.GET, "s-end_date")
        name = get_param(request.GET, "s-name")
        status = get_param(request.GET, "s-status")

        items = search(project.uuid, ini_date, end_date, name, status, s_id)

        context={'total_items': len(items), 'items': items[0:ITEMS_PER_PAGE], 'status': status, 'index': ITEMS_PER_PAGE}
        return render(request, "bookings/tpv-orders/order-list.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def orders_page(request):
    try:
        project = get_or_none(Project, request.project_id)
        form = get_param(request.GET, "s-form")
        ini_date = get_param(request.GET, "s-ini_date")
        end_date = get_param(request.GET, "s-end_date")
        name = get_param(request.GET, "s-name")
        status = get_param(request.GET, "s-status")
        page = get_param(request.GET, "page", "0")
        ini = int(page)*ITEMS_PER_PAGE
        end = ini+ITEMS_PER_PAGE

        items = search(project.uuid, ini_date, end_date, name, status)
        #items = search(project.uuid, form, ini_date, end_date, name, status)

        context={'total_items': len(items), 'items': items[ini:end], 'status': status, 'index': end}
        return render(request, "bookings/tpv-orders/order-page.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


@group_required("projects")
def orders_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        context = get_orders_project_context(project)
        context['index'] = ITEMS_PER_PAGE
        context['active'] = "orders_tpv" 
        return render (request, "bookings/tpv-orders/orders.html", context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-orders_by_project] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

