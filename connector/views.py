from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 
from datetime import datetime

from padword.commons import show_exc, get_or_none
from padword.email_lib import send_email
from padword.decorators import group_required
from .models import ProjectAvaibookUser
from .avantio_lib import get_booking_list, get_booking_notif, send_link
from .avaibook_lib import get_accommodation_list, get_booking_list as av_get_booking_list

import os


'''
    Avantio
'''
@group_required("admins", "projects")
def avantio_get_booking_list(request, project_uuid):
    try:
        booking_list, err = get_booking_list(project_uuid)

        pau = ProjectAvantioUser.objects.filter(project_uuid=project_uuid).first()
        if pau != None and pau.email != "":
            result = "Importación {} {}\n".format(pau.project.name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            result += "-----------------------------------------------------"
            result += render_to_string('avantio/booking-log.html', {'booking_list': booking_list, "error": err})
            subject = "Importación {} {}".format(pau.project.name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            send_email(subject, result, "no-reply@padword.es", [pau.email])

        return render(request, 'avantio/booking-list.html', {'booking_list': booking_list, "error": err})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def avantio_get_booking_notif(request, project_uuid):
    try:
        booking_list = get_booking_notif(project_uuid)
        return render(request, 'avantio/booking-notif.html', {'booking_list': booking_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


@group_required("admins")
def avantio_send_link(request, project_uuid, guest_uuid):
    try:
        resp = send_link(project_uuid, guest_uuid)
        return HttpResponse(resp)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

'''
    Avaibook
'''
@group_required("admins", "projects")
def avaibook_get_booking_list(request, project_uuid):
    try:
        pau = get_or_none(ProjectAvaibookUser, project_uuid, "project_uuid")
        booking_list = av_get_booking_list(pau)
        return render(request, 'avaibook/booking-list.html', {'booking_list': booking_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def avaibook_get_accommodation_list(request, project_uuid):
    try:
        pau = get_or_none(ProjectAvaibookUser, project_uuid, "project_uuid")
        item_list = get_accommodation_list(pau)
        return render(request, 'avaibook/accommodation-list.html', {'item_list': item_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

'''
    Cron Logs
'''
@group_required("admins")
def cron_log(request):
    f = open(os.path.join(settings.BASE_DIR, "cron.log"), "r", encoding='utf-8')
    text = f.read()
    return render(request, 'cron-log.html', {'text': text.replace("\n", "<br/>"),})

@group_required("admins")
def test_email(request):
    send_email("test", "test", "no-reply@padword.es", ["zebenperez@gmail.com"])
    return HttpResponse("Ok")
