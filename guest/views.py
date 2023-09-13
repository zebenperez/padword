from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 
from django.db.models import Q
import datetime

from .models import *
from web.lock_lib import ShLock
from padword.commons import show_exc, get_or_none, get_float, new_ui_slug, translate, user_in_group, get_param, reverse_cardkey, set_session
from padword.decorators import group_required
from bookings.models import GuestUser
import web.models as webmod 

ITEMS_PER_PAGE=20


@group_required("admins")
def index(request):
    try:
        guests = Guest.objects.all()
        registers = [{'name':comp.name,'surname':comp.surname} for comp in guests]

        return JsonResponse({'results':registers, 'error':0})
        #return JsonResponse({'results':serializers.serialize("json", companies, fields=('uuid','name')), 'error':0})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

'''
    Guests
'''
def get_guest_items(request, ini=0, end=ITEMS_PER_PAGE):
    filters_to_search = ["name__icontains", "room", "surname__icontains", "email__icontains", "mobile__icontains"]
    search_value = request.session["guest_search_name"] if "guest_search_name" in request.session else ""
    project_uuid = request.session["guest_search_project"] if "guest_search_project" in request.session else ""
    #project_uuid = request.session["project_uuid"] if "project_uuid" in request.session else ""

    full_query = Q()
    if search_value != "":
        for myfilter in filters_to_search:
            full_query |= Q(**{myfilter: search_value})
        #projects_uuid = [item.uuid for item in webmod.Project.objects.filter(name__icontains = search_value)]
        #full_query |= Q(**{'project_id__in': projects_uuid})
        rooms_number = [item.number for item in webmod.Room.objects.filter(alias__icontains = search_value)]
        full_query |= Q(**{'room__in': rooms_number})
    if project_uuid != "":
        full_query &= Q(**{'project_id': project_uuid})

    items = Guest.objects.filter(full_query) if len(full_query) > 0 else Guest.objects.all()
    #items = Guest.objects.filter(deleted=0).filter(full_query) if len(full_query) > 0 else Guest.objects.filter(deleted=0)
    return items[ini:end], items.count()
    #return Guest.objects.filter(full_query) if len(full_query) > 0 else Guest.objects.all()

@group_required("admins")
def guests(request):
    try:
        request.session["project_uuid"] = ""
        items, total_count = get_guest_items(request)
        #total_count = items.count()

        project_list = Project.objects.filter(active=1).order_by('name')
        context = {'total_items': total_count, 'items': items, 'index': ITEMS_PER_PAGE, 'project_list': project_list, 'active': 'guests'}
        #context = {'total_items': total_count, 'items': items[0:ITEMS_PER_PAGE], 'page': 0}
        return render (request, "guest/guests.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})
        #return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins")
def guest_search(request):
    try:
        set_session(request, "guest_search_name")
        set_session(request, "guest_search_project")
        items, total_count = get_guest_items(request)

        context = {'total_items': total_count, 'items': items, 'index': ITEMS_PER_PAGE}
        #context = {'total_items': items.count(), 'items': items[0:ITEMS_PER_PAGE], 'page': 0}
        context["project_uuid"] = get_param(request.GET, "project_uuid")
        return render(request, "guest/guest-list.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def guest_page(request):
    try:
        #set_session(request, "guest_search_name")
        page = get_param(request.GET, "page", 0)
        ini = int(page)*ITEMS_PER_PAGE
        end = ini+ITEMS_PER_PAGE
        items, total_count = get_guest_items(request, ini, end)

        context = {'total_items': total_count, 'items': items, 'index': end}
        #context = {'total_items': items.count(), 'items': items[ini:end], 'page': page, 'hide_btn': hide_btn}
        context["project_uuid"] = get_param(request.GET, "project_uuid")
        return render(request, "guest/guest-page.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def guest_form(request):
    try:
        date = datetime.datetime.now().replace(hour=12, minute=00)
        if "obj_id" in request.GET:
            obj = get_or_none(Guest, request.GET["obj_id"])  
        else: 
            obj = Guest.objects.create(UUID = new_ui_slug(Guest, "UUID"), check_in = date, check_out = date)
        regime_list = [item.regime for item in obj.project.regimes.all()]
        return render(request, "guest/guest-form.html", {'obj': obj, 'temp_range': range(16,26), 'regime_list': regime_list,})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def guest_details(request, obj_id=""):
    try:
        date = datetime.datetime.now().replace(hour=12, minute=00)
        obj = Guest.objects.create(UUID=new_ui_slug(Guest, "UUID"), check_in=date, check_out=date) if obj_id == "" else get_or_none(Guest, obj_id)
        regime_list = [item.regime for item in obj.project.regimes.all()]
        return render(request, "guest/guest-details.html", {'obj': obj, 'temp_range': range(16,26), 'regime_list': regime_list,})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


#@group_required("admins")
#def guest_form_simple(request):
#    try:
#        date = datetime.datetime.now().replace(hour=12, minute=00)
#        obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else Guest.objects.create(UUID = new_ui_slug(Guest), check_in = date, check_out = date)
#        return render(request, "guest/guest-form-simple.html", {'obj': obj,})
#    except Exception as e:
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def guest_remove(request, obj_id):
    obj = get_or_none(Guest, obj_id)
    if obj != None:
        GuestUser.delete_by_guest(obj.UUID)
        obj.delete_all()
    return redirect(guests)

    #project_uuid = request.GET["project_uuid"] if "project_uuid" in request.GET else None
    #obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else None
    #if obj != None:
    #    GuestUser.delete_by_guest(obj.UUID)
    #    obj.delete_all()
        #obj.remove_all_key_codes()
        #obj.remove_all_key_cards()
        #obj.delete()

    #items = Guest.objects.all() if project_uuid == None else Guest.objects.filter(project_id=project_uuid)
    #items, total_count = get_guest_items(request)
    #return render(request, "guest/guest-list.html", {'items':items, 'project_uuid': project_uuid})

@group_required("admins")
def guest_soft_remove(request, obj_id):
    obj = get_or_none(Guest, obj_id) 
    if obj != None:
        GuestUser.delete_by_guest(obj.UUID)
        obj.delete_soft()
    return redirect(guests)

    #project_uuid = request.GET["project_uuid"] if "project_uuid" in request.GET else None
    #obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else None
    #if obj != None:
    #    GuestUser.delete_by_guest(obj.UUID)
    #    obj.delete_soft()
        #obj.remove_all_key_codes()
        #obj.remove_all_key_cards()
        #obj.deleted = 1
        #obj.save()

    #items, total_count = get_guest_items(request)
    #return render(request, "guest/guest-list.html", {'items':items, 'project_uuid': project_uuid})

#@group_required("admins","projects")
#def guest_pagination(request):
#    try:
#        set_session(request, "guest_search_name")
#        page = get_param(request.GET, "s-page", "0")
#        items = get_guest_items(request)
#
#        context = {}
#        context['total_items'] = items.count()
#        context['items'] = items[int(page)*ITEMS_PER_PAGE:(int(page) + 1)*ITEMS_PER_PAGE]
#        context['page'] = page 
#        return render(request, "guest/guest-page.html", context)
#    except Exception as e:
#        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins","projects")
def guest_update_code(request):
    try:
        guest = get_or_none(Guest, request.GET["obj_id"]) 
        if guest == None:
            return render(request, "error_exception.html", {'exc': _('Guest not found!')})

        err = guest.change_all_key_code(guest.mobile_to_code())
        return render(request, "guest/keys/guest-keys.html", {'obj': guest, "err": err})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


#@group_required("admins","projects")
#def guest_save_date(request):
#    try:
#        err = ""
#        guest = get_or_none(Guest, request.GET["obj_id"]) 
#        if guest == None:
#            return render(request, "error_exception.html", {'exc': _('Guest not found!')})
#
#        field = request.GET["field"]
#        value = request.GET["value"]
#        val = ""
#        if "-" in value:
#            val = datetime.datetime.strptime("{} {}".format(value, getattr(guest, field).strftime('%H:%M')), '%Y-%m-%d %H:%M')
#        if ":" in value:
#            val = datetime.datetime.strptime("{} {}".format(getattr(guest, field).strftime('%Y-%m-%d'), value), '%Y-%m-%d %H:%M')
#        setattr(guest, field, val)
#
#        guest.save()
#        guest.change_all_key_code_date()
#        guest.change_all_key_card_date()
#        #return HttpResponse("")
#        return render(request, "guest/guest-details-tabs.html", {'obj': guest, 'temp_range': range(16,26)})
#    except Exception as e:
#        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins","projects")
def guest_save_date(request):
    try:
        err = ""
        guest = get_or_none(Guest, request.GET["obj_id"]) 
        if guest == None:
            return render(request, "error_exception.html", {'exc': _('Guest not found!')})

        check_in = get_param(request.GET, "check_in")
        check_in_time = get_param(request.GET, "check_in_time")
        check_out = get_param(request.GET, "check_out")
        check_out_time = get_param(request.GET, "check_out_time")
        c_in = datetime.datetime.strptime("{} {}".format(check_in, check_in_time), '%Y-%m-%d %H:%M')
        c_out = datetime.datetime.strptime("{} {}".format(check_out, check_out_time), '%Y-%m-%d %H:%M')
        if c_out < c_in:
            return render(request, "error_exception.html", {'exc': _('Checkout can not be less than checkin!')})

        guest.check_in = c_in
        guest.check_out = c_out
        guest.save()
        guest.change_all_key_code_date()
        guest.change_all_key_card_date()
        return render(request, "guest/guest-details-tabs.html", {'obj': guest, 'temp_range': range(16,26)})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins","projects")
def guest_save_room(request):
    try:
        err = ""
        guest = get_or_none(Guest, request.GET["obj_id"]) 
        if guest == None:
            return render(request, "error_exception.html", {'exc': _('Guest not found!')})

        value = request.GET["value"]
        if value == "":
            guest.room = value
            guest.save()
            guest.remove_all_key_codes()
            guest.remove_all_key_cards()
            guest.remove_all_sensibo_devices()
        else:
            err = guest.change_room(value)
            guest.change_sensibo_devices(value)
        return render(request, "guest/keys/guest-keys.html", {'obj': guest, "err": err})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_room_autocomplete(request):
    try:
        value = get_param(request.GET, "value")
        obj_id = get_param(request.GET, "obj_id")
        guest = get_or_none(Guest, obj_id)
        items = []
        if value != "":
            items = webmod.Room.objects.filter(project_uuid=guest.project_id).filter(Q(number__icontains=value) | Q(alias__icontains=value))

        return render(request, "guest/room-list.html", {'items': items, 'obj': guest, 'value':value})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_set_regime(request):
    try:
        value = get_param(request.GET, "value")
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        guest.regimes.all().delete()
        if value != "":
            regime = get_or_none(Regime, value)
            gr = GuestRegime.objects.create(regime=regime, guest=guest)
        return render(request, "guest/guest-details-tabs.html", {'obj': guest, 'temp_range': range(16,26)})
        #return HttpResponse(_("Saved!"))
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

'''
    Guests by projects
'''
def delete_expired(project):
    limit = datetime.datetime.now() - datetime.timedelta(days=project.guest_delete)
    guest_list = Guest.objects.filter(project_id=project.uuid, deleted=0, check_out__lt=limit)
    for guest in guest_list:
        GuestUser.delete_by_guest(guest.UUID)
        guest.delete_soft()
        #guest.deleted = 1
        #guest.save()

def get_guest_items_by_project(request, project_uuid, ini=0, end=ITEMS_PER_PAGE):
    filters_to_search = ["name__icontains", "room", "surname__icontains", "email__icontains", "mobile__icontains"]
    search_value = request.session["guest_search_name"] if "guest_search_name" in request.session else ""

    full_query = Q()
    if search_value != "":
        for myfilter in filters_to_search:
            full_query |= Q(**{myfilter: search_value})
        rooms_number = [item.number for item in webmod.Room.objects.filter(alias__icontains = search_value)]
        full_query |= Q(**{'room__in': rooms_number})

    #items = Guest.objects.filter(project_id=project_uuid).filter(full_query)
    items = Guest.objects.filter(project_id=project_uuid, deleted=0).filter(full_query)
    return items[ini:end], items.count()
    #return Guest.objects.filter(project_id=project_uuid).filter(full_query)

@group_required("projects")
def guests_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        #items = Guest.objects.filter(project_id = project.uuid)
        #delete_expired(project)
        items, total_count = get_guest_items_by_project(request, project.uuid)
        limit = datetime.datetime.now() - datetime.timedelta(days=project.guest_delete)

        context = {'total_items': total_count, 'items': items, 'index': ITEMS_PER_PAGE, 'project': project, 'limit': limit, 'active': 'guests'}
        #print(context)
        #context = {'total_items': items.count(), 'page': 0, 'project_uuid':project.uuid, 'items': items[0:ITEMS_PER_PAGE]}
        return render (request, "guest-by-project/guests.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def guest_search_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        set_session(request, "guest_search_name")
        #items = get_guest_items_by_project(request, project.uuid)
        items, total_count = get_guest_items_by_project(request, project.uuid)

        context = {'total_items': total_count, 'items': items, 'index': ITEMS_PER_PAGE}
        #context = {'total_items': items.count(), 'items': items[0:ITEMS_PER_PAGE], 'page': 0, 'project_uuid': project.uuid}
        return render(request, "guest-by-project/guest-list.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def guest_page_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        #set_session(request, "guest_search_name")
        page = get_param(request.GET, "page", 0)
        ini = int(page)*ITEMS_PER_PAGE
        end = ini+ITEMS_PER_PAGE
        items, total_count = get_guest_items_by_project(request, project.uuid, ini, end)

        context = {'total_items': total_count, 'items': items, 'index': end}
        context["project_uuid"] = get_param(request.GET, "project_uuid")
        return render(request, "guest-by-project/guest-page.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


@group_required("projects")
def guest_form_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        if "obj_id" in request.GET:
            obj = get_or_none(Guest, request.GET["obj_id"]) 
        else:
            date = datetime.datetime.now().replace(hour=12, minute=00)
            obj = Guest.objects.create(UUID = new_ui_slug(Guest, "UUID"), project_id = project.uuid, check_in = date, check_out = date)
        return render(request, "guest-by-project/guest-form.html", {'obj': obj, 'project_uuid': project.uuid, 'temp_range': range(16,26)})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def guest_details_by_project(request, obj_id=""):
    try:
        project = get_or_none(Project, request.project_id)
        if obj_id != "":
            obj = get_or_none(Guest, obj_id)  
        else: 
            date = datetime.datetime.now().replace(hour=12, minute=00)
            obj = Guest.objects.create(UUID = new_ui_slug(Guest, "UUID"), project_id = project.uuid, check_in = date, check_out = date)
        regime_list = [item.regime for item in obj.project.regimes.all()]
        context = {'obj': obj, 'project_uuid': project.uuid, 'temp_range': range(16,26), 'regime_list': regime_list,}
        return render(request, "guest-by-project/guest-details-by-project.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def guest_remove_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else None
        if obj != None:
            GuestUser.delete_by_guest(obj.UUID)
            obj.delete_all()
            #obj.remove_all_key_codes()
            #obj.remove_all_key_cards()
            #obj.delete()

        items = get_guest_items_by_project(request, project.uuid)
        return render(request, "guest-by-project/guest-list.html", {'items':items, 'project_uuid': project.uuid})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def guest_soft_remove_by_project(request, obj_id):
    try:
        project = get_or_none(Project, request.project_id)
        obj = get_or_none(Guest, obj_id) 
        #obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else None
        if obj != None:
            GuestUser.delete_by_guest(obj.UUID)
            obj.delete_soft()

        return redirect(guests_by_project)
        #items, total_count = get_guest_items_by_project(request, project.uuid)
        #return render(request, "guest-by-project/guest-list.html", {'items':items, 'project_uuid': project.uuid})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def guest_soft_remove_all_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        limit = datetime.datetime.now() - datetime.timedelta(days=project.guest_delete)
        guest_list = Guest.objects.filter(project_id=project.uuid, deleted=0, check_out__lt=limit)
        msg = ""
        for guest in guest_list:
            msg += "<br/>Deleting guest: {} {}<br/>".format(guest.name, guest.surname)
            GuestUser.delete_by_guest(guest.UUID)
            msg += guest.delete_soft()
            msg += "<br/>-- Guest deleted."
            msg += "<br/>-----------------------"

        items, total_count = get_guest_items_by_project(request, project.uuid)
        return render(request, "guest-by-project/guest-list.html", {'items':items, 'project_uuid': project.uuid, 'msg': msg})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


'''
    Devices
'''
@group_required("admins", "projects")
def devices(request):
    try:
        if user_in_group(request.user, "projects"):
            if not hasattr(request, "project_id"):
                return render(request, "error_exception.html", {'exc': _('Project not found!')})
            project = get_or_none(Project, request.project_id)
            items = webmod.Device.by_project(project)
        elif user_in_group(request.user, "admins"):
            items = webmod.Device.objects.all()
        else:
            return render(request, "error_exception.html", {'exc': _('This user have not permission for this section!')})
        total_count = items.count()

        return render (request, "device/devices.html",{'items':items[0:20], 'page':0, 'n_items':total_count})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})
        #return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
def device_search(request):
    try:
        filters_to_search = ["alias__icontains", "imei__icontains"]
        search_value = request.GET["s-name"] if "s-name" in request.GET else ""
        if search_value != "":
            items = webmod.Device.objects.none()
            for myfilter in filters_to_search:
                kwargs = {}
                kwargs[myfilter] = search_value
                items = items.union(webmod.Device.objects.filter(**kwargs))

            #channels = webmod.Channel.objects.filter(name__icontains = search_value)
            #items = items.union(Guest.by_channel(channels))
            #projects = webmod.Project.objects.filter(name__icontains = search_value)
            #items = items.union(Guest.by_project(projects))
        else:
            items = webmod.Device.objects.all()
        return render(request, "device/device-list.html", {'items': items,})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
def device_form(request):
    try:
        if not "obj_id" in request.GET:
            return render(request, 'error_exception.html', {'exc':_('Object not found!')})
        obj = get_or_none(webmod.Device, request.GET["obj_id"]) 
        return render(request, "device/device-form.html", {'obj': obj,})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def device_room(request):
    try:
        if not "obj_id" in request.GET:
            return render(request, 'error_exception.html', {'exc':_('Object not found!')})
        obj = get_or_none(webmod.Device, request.GET["obj_id"]) 
        item_list = Guest.rooms_assigned(obj.project.uuid)
        return render(request, "device/device-room.html", {'obj': obj, 'item_list': item_list})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def device_remove(request):
    obj = get_or_none(webmod.Device, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()

    items = webmod.Device.objects.all()
    return render(request, "device/device-list.html", {'items':items,})

@group_required("admins","projects")
def device_pagination(request, page=0):
    try:
        items = webmod.Device.objects.all()
        items = items[page*20:(page+1)*20]
        return render(request, "device/device-page.html", {'items':items, 'page':page})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

'''
   Notifications 
'''
def get_notification_guests(value, notification, project):
    guest_ids = notification.guests.all().values_list('guest__id', flat=True)

    filters_to_search = ["name__icontains", "room", "surname__icontains", "email__icontains"]
    now = datetime.datetime.now()
    #now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    values_filter = Q()
    for myfilter in filters_to_search:
        values_filter |= Q(**{myfilter: value})
            
    kwargs = {'check_in__lte': now, 'check_out__gte': now}
    if project != None:
        kwargs["project_id"] = project.uuid

    return Guest.objects.filter(values_filter).filter(**kwargs).exclude(id__in=guest_ids)

def get_notifications(values):
    try:
        project = get_or_none(Project, values.project_id)
        return Notification.objects.filter(project_uuid=project.uuid)
    except:
        return Notification.objects.all()

def get_notifications_project_uuid(values):
    try:
        project = get_or_none(Project, values.project_id)
        return project.uuid
    except:
        return ""

@group_required("admins", "projects")
def notifications(request):
    try:
        items = get_notifications(request)
        context = {'total_items': items.count(), 'items': items[0:ITEMS_PER_PAGE], 'page': 0, 'active': 'notifications'}
        return render (request, "guest/notifications/notifications.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def notification_search(request):
    try:
        page = "0"
        search_value = request.GET["s-name"] if "s-name" in request.GET else ""
        items = get_notifications(request)
        if search_value != "":
            filters_to_search = ["guest__name__icontains", "guest__room"]
            values_filter = Q()
            for myfilter in filters_to_search:
                values_filter |= Q(**{myfilter: search_value})
            gu_items = GuestNotification.objects.filter(values_filter).values_list('notification__id', flat=True)
            items = items.filter(id__in = gu_items)
 
        context = {'total_items':  items.count(), 'items': items[int(page)*ITEMS_PER_PAGE:(int(page) + 1)*ITEMS_PER_PAGE], 'page': 0}
        return render(request, "guest/notifications/notification-list.html", context)
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
def notification_form(request):
    try:
        project_uuid = get_notifications_project_uuid(request)
        obj = get_or_none(Notification, request.GET["obj_id"]) if "obj_id" in request.GET else Notification.objects.create(project_uuid=project_uuid)
        return render(request, "guest/notifications/notification-form.html", {'obj': obj,})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def notification_remove(request):
    obj = get_or_none(Notification, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()

    items = get_notifications(request)
    return render(request, "guest/notifications/notification-list.html", {'items':items[0:ITEMS_PER_PAGE]})

@group_required("admins", "projects")
def notification_send(request):
    obj = get_or_none(Notification, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.public = True
        obj.save()

    items = get_notifications(request)
    return render(request, "guest/notifications/notification-list.html", {'items':items[0:ITEMS_PER_PAGE]})


@group_required("admins", "projects")
def notification_pagination(request):
    try:
        page = get_param(request.GET, "s-page", "0")
        items = get_notifications(request)

        context = {'total_items': items.count(), 'page': page, 'items': items[int(page)*ITEMS_PER_PAGE:(int(page) + 1)*ITEMS_PER_PAGE]}
        return render(request, "guest/notifications/notification-page.html", context)
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def notification_autocomplete(request):
    try:
        value = get_param(request.GET, "value")
        notification_id = get_param(request.GET, "obj_id")
        notification = get_or_none(Notification, notification_id)
        items = []
        if value != "":
            try:
                project = get_or_none(Project, request.project_id)
                items = get_notification_guests(value, notification, project)
            except:
                items = get_notification_guests(value, notification, None)

        return render(request, "guest/notifications/guest-list.html", {'items': items, 'notification': notification.id})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def notification_add_guest(request):
    try:
        guest_id = get_param(request.GET, "obj_id")
        guest = get_or_none(Guest, guest_id)
        notification_id = get_param(request.GET, "notification")
        notification = get_or_none(Notification, notification_id)
        if notification != None and guest != None:
            GuestNotification.objects.create(guest=guest, notification=notification)
        return render(request, "guest/notifications/notification-guests.html", {'obj': notification})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def notification_remove_guest(request):
    try:
        gn_id = get_param(request.GET, "obj_id")
        gn = get_or_none(GuestNotification, gn_id)
        notification = None
        if gn != None:
            notification = gn.notification
            gn.delete()
        return render(request, "guest/notifications/notification-guests.html", {'obj': notification})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


'''
   Chat
'''
#def get_sender_msg(guest, sender, date=""):
#    return guest.get_messages(False, sender, date)
def get_messages(guest, guest_msg):
    return {'messages': guest.get_messages(guest_msg != "False"), 'guest_msg': guest_msg}

@group_required("admins", "projects")
def show_chat(request):
    guest = get_or_none(Guest, request.GET["guest"])
    context = get_messages(guest, request.GET["guest_msg"])
    context["guest"] = guest
    return render(request, "guest/chat.html", context)

@group_required("admins", "projects")
def message_send(request):
    guest = get_or_none(Guest, request.GET["guest"])
    guest_msg = request.GET["guest_msg"]
    if guest != None:
        Message.objects.create(guest=guest, guest_msg=(guest_msg != "False"), msg=request.GET["value"])
    return render(request, "guest/messages.html", get_messages(guest, guest_msg))

@group_required("admins", "projects")
def message_remove(request):
    msg = get_or_none(Message, request.GET["obj_id"])
    guest = msg.guest
    guest_msg = "True" if msg.guest_msg else "False"
    msg.delete()
    return render(request, "guest/messages.html", get_messages(guest, guest_msg))

@group_required("admins", "projects", "guests")
def messages_check(request):
    guest = get_or_none(Guest, request.GET["guest"])
    return render(request, "guest/messages.html", get_messages(guest, request.GET["guest_msg"]))
    #date = datetime.datetime.min
    #if "date" in request.GET and request.GET["date"] != "":
    #    date = datetime.datetime.strptime(request.GET["date"], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(seconds=1)
    #messages = get_sender_msg(guest, request.user, date) if guest_msg == "False" else guest.get_messages(True, None, date)
    #return render(request, "guest/messages.html", {'messages': get_messages(guest_msg), 'guest_msg': request.GET["guest_msg"]})

'''
   Keys
'''
@group_required("admins", "projects")
def key_open(request):
    lock = get_or_none(Lock, request.GET["obj_id"])
    msg = lock.open_lock()
    msg = msg if msg != True else ""
    return HttpResponse(msg)

@group_required("admins", "projects")
def key_change_code(request):
    try:
        key = get_or_none(KeyCode, request.POST["key_code"])
        code = request.POST["code"]

        key.guest.change_all_key_code(code)
        return render(request, "guest/keys/guest-keys.html", {"obj": key.guest})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def key_add_card(request):
    try:
        guest = get_or_none(Guest, request.GET["guest_id"])
        code = reverse_cardkey(request.GET["value"])

        guest.add_all_key_card(code)
        return render(request, "guest/keys/guest-keys.html", {"obj": guest})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def key_remove_card(request):
    try:
        key = get_or_none(KeyCard, request.GET["obj_id"])
        guest = key.guest

        key.guest.remove_all_key_cards(key.code)
        return render(request, "guest/keys/guest-keys.html", {"obj": guest})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


