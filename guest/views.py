from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 
from django.db.models import Q
import datetime

from .models import *
from web.lock_lib import ShLock
from padword.commons import show_exc, get_or_none, new_ui_slug, translate, user_in_group, get_param
from padword.decorators import group_required
from bookings.models import GuestUser
import web.models as webmod 

ITEMS_PER_PAGE=20


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
@group_required("admins")
def guests(request):
    try:
        #items= Guest.objects.filter(check_out__gte = datetime.datetime.now())
        items= Guest.objects.all()
        total_count = items.count()

        context = {}
        page = 0
        context['total_items'] = items.count()
        context['items'] = items[int(page)*ITEMS_PER_PAGE:(int(page) + 1)*ITEMS_PER_PAGE]
        context['page'] = 0


        return render (request, "guest/guests.html", context)
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
def guest_search(request):
    try:
        project_uuid = request.GET["project_uuid"] if "project_uuid" in request.GET else ""
        filters_to_search = ["name__icontains", "room", "surname__icontains", "email__icontains", "mobile__icontains"]
        search_value = request.GET["s-name"] if "s-name" in request.GET else ""
        page = "0"
        if search_value != "":
            items = Guest.objects.none()
            for myfilter in filters_to_search:
                kwargs = {}
                kwargs[myfilter] = search_value
                if project_uuid != "":
                    items = items | Guest.objects.filter(project_id=project_uuid).filter(**kwargs)
                else:
                    items = items | Guest.objects.filter(**kwargs)

            projects = webmod.Project.objects.filter(name__icontains = search_value)
            items |= Guest.by_project(projects)

        else:
            if project_uuid != "":
                items = Guest.objects.filter(project_id=project_uuid)
            else:
                #items = Guest.objects.filter(check_out__gte = datetime.datetime.today())
                items = Guest.objects.all()
        context = {}
        context['project_uuid'] = project_uuid
        context['total_items'] = items.count()
        context['items'] = items[int(page)*ITEMS_PER_PAGE:(int(page) + 1)*ITEMS_PER_PAGE]
        context['page'] = 0
        return render(request, "guest/guest-list.html", context)
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins")
def guest_form(request):
    try:
        date = datetime.datetime.now().replace(hour=12, minute=00)
        obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else Guest.objects.create(UUID = new_ui_slug(Guest), check_in = date, check_out = date)
        return render(request, "guest/guest-form.html", {'obj': obj,})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def guest_form_simple(request):
    try:
        date = datetime.datetime.now().replace(hour=12, minute=00)
        obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else Guest.objects.create(UUID = new_ui_slug(Guest), check_in = date, check_out = date)
        return render(request, "guest/guest-form-simple.html", {'obj': obj,})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_remove(request):
    project_uuid = request.GET["project_uuid"] if "project_uuid" in request.GET else None
    obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        GuestUser.delete_by_guest(obj.UUID)
        obj.delete()

    items = Guest.objects.all() if project_uuid == None else Guest.objects.filter(project_id=project_uuid)
    return render(request, "guest/guest-list.html", {'items':items, 'project_uuid': project_uuid})

@group_required("admins","projects")
def guest_pagination(request):
    try:
        name = get_param(request.GET, "s-name")
        page = get_param(request.GET, "s-page", "0")
        project_uuid = get_param(request.GET, "project_uuid", "")
        if name != "":
            items = Guest.objects.none()
            filters_to_search = ["name__icontains", "room", "surname__icontains", "email__icontains"]
            for myfilter in filters_to_search:
                kwargs = {}
                kwargs[myfilter] = name
                items |= Guest.objects.filter(**kwargs)

            projects = webmod.Project.objects.filter(name__icontains = name)
            items != Guest.by_project(projects)
        else:
            items = Guest.objects.all()

        if project_uuid != "":
            items = items.filter(project_id=project_uuid)

        context = {}
        context['total_items'] = items.count()
        context['items'] = items[int(page)*ITEMS_PER_PAGE:(int(page) + 1)*ITEMS_PER_PAGE]
        context['page'] = page 
        return render(request, "guest/guest-page.html", context)
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins","projects")
def guest_save_room(request):
    try:
        err = ""
        guest = get_or_none(Guest, request.GET["obj_id"]) 
        value = request.GET["value"]
        guest.room = value
        guest.save()
        lock = webmod.Lock.objects.filter(room = value, project_uuid = guest.project_id).first()
        if lock != None and guest != None:
            code_id = lock.set_code(guest.mobile[-4:], guest.check_in, guest.check_out)
            if not "Error" in str(code_id):
                key = Key.objects.create(lock = lock, guest = guest, code = guest.mobile[-4:], code_id = code_id)
            else:
                err = code_id
            #key, created = Key.objects.get_or_create(lock = lock, guest = guest, code = guest.mobile[-4:], code_id = code_id)
        else:
            for key in guest.keys.all():
                errcode = key.lock.remove_code(key.code_id)
                if errcode == 0:
                    key.delete()
 
            #guest.keys.all().delete()
        return render(request, "guest/keys/guest-keys.html", {'obj': guest, "err": err})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

'''
    Guests by projects
'''
@group_required("admins", "projects")
def guests_by_project(request, project_id):
    try:
        project = get_or_none(Project, project_id, "uuid")
        #items= Guest.objects.filter(check_out__gte = datetime.datetime.now())
        items = Guest.objects.filter(project_id = project_id)
        total_count = items.count()

        context = {}
        page = 0
        context['total_items'] = items.count()
        context['items'] = items[int(page)*ITEMS_PER_PAGE:(int(page) + 1)*ITEMS_PER_PAGE]
        context['page'] = 0
        context['project_uuid'] = project_id

        return render (request, "guest/guests.html", context)
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
def guest_form_by_project(request):
    try:
        project_uuid = request.GET["project_uuid"]
        date = datetime.datetime.now().replace(hour=12, minute=00)
        obj = get_or_none(Guest, request.GET["obj_id"]) if "obj_id" in request.GET else Guest.objects.create(UUID = new_ui_slug(Guest), project_id = project_uuid, check_in = date, check_out = date)
        return render(request, "guest/guest-form.html", {'obj': obj, 'project_uuid': project_uuid})
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
        context = {'total_items': items.count(), 'items': items[0:ITEMS_PER_PAGE], 'page': 0}
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

    items = Notification.objects.all() 
    return render(request, "guest/notifications/notification-list.html", {'items':items[0:ITEMS_PER_PAGE]})

@group_required("admins", "projects")
def notification_send(request):
    obj = get_or_none(Notification, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.public = True
        obj.save()

    items = Notification.objects.all() 
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
    sh_lock = ShLock()
    msg = sh_lock.open_lock_by_id(request.GET["obj_id"])
    msg = _("Opened") if msg else msg
    return HttpResponse(msg)

@group_required("admins", "projects")
def key_change_code(request):
    try:
        key = get_or_none(Key, request.POST["key"])
        code = request.POST["code"]

        errcode = key.lock.change_code(key.code_id, code, key.guest.check_in, key.guest.check_out)
        if errcode == 0:
            key.code = code
            key.save()
        return render(request, "guest/keys/guest-key-details.html", {"item": key})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def key_remove(request):
    try:
        key = get_or_none(Key, request.GET["obj_id"])

        errcode = key.lock.remove_code(key.code_id)
        if errcode == 0:
            key.delete()
            return HttpResponse("")
        return render(request, "guest/keys/guest-key-details.html", {"item": key})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


#def get_key_list(obj):
#    sh_lock = ShLock()
#    return sh_lock.get_locks(obj.get_locks_id())
#
#@group_required("admins", "projects")
#def keys(request):
#    try:
#        obj = get_or_none(Guest, request.GET["obj_id"]) 
#        return render(request, "guest/keys/guest-keys.html", {'obj': obj, 'key_list': get_key_list(obj)})
#    except Exception as e:
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})
#
#@group_required("admins", "projects")
#def key_assign(request):
#    try:
#        obj = get_or_none(Guest, request.GET["obj_id"]) 
#        if obj != None:
#            Key.objects.create(lock = request.GET["lock"], guest = obj)
#        return render(request, "guest/keys/guest-keys.html", {'obj': obj, 'key_list': get_key_list(obj)})
#    except Exception as e:
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})
#
#@group_required("admins", "projects")
#def key_remove(request):
#    try:
#        key = get_or_none(Key, request.GET["obj_id"]) 
#        obj = key.guest
#        key.delete()
#        return render(request, "guest/keys/guest-keys.html", {'obj': obj, 'key_list': get_key_list(obj)})
#    except Exception as e:
#        print(e)
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})
#
