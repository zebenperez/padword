from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden 
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _ 
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from datetime import datetime
from secrets import compare_digest

from padword.commons import show_exc, get_or_none
from padword.email_lib import send_email
from padword.decorators import group_required
from web.models import Project
from .models import ProjectAvantioUser, ProjectAvaibookUser
from .avantio_lib import get_booking_list, get_booking_notif, send_link
from .avaibook_lib import get_accommodation_list, get_booking_list as av_get_booking_list, WEBHOOK_TOKEN

import json, os


'''
    Avantio
'''
@group_required("admins", "projects")
def avantio_get_booking_list(request, project_uuid):
    try:
        booking_list, err = get_booking_list(project_uuid)

        pau = ProjectAvantioUser.objects.filter(project_uuid=project_uuid).first()
        if pau != None and pau.email != "":
            project = get_or_none(Project, project_uuid, "uuid")
            result = "Importación {} {}\n".format(project.name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            result += "-----------------------------------------------------"
            result += render_to_string('avantio/booking-log.html', {'booking_list': booking_list, "error": err})
            subject = "Importación {} {}".format(project.name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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

@csrf_exempt
@require_POST
#@non_atomic_requests
def avaibook_get_booking(request):
    f = open(os.path.join(settings.BASE_DIR, "avaibook.log"), "a", encoding='utf-8')
    f.write("\n---------------------------------------")
    f.write("\n{} - Recibida reserva de avantio".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    given_token = request.headers.get("Avaibook-Webhook-Token", "")
    if not compare_digest(given_token, WEBHOOK_TOKEN):
        f.write("\nToken no valido".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        return HttpResponseForbidden(
            "Incorrect token in Avaibook-Webhook-Token header.",
            content_type="text/plain",
        )

    booking = json.loads(request.body)
    f.write("\n{}".format(booking))
    return HttpResponse("Message received okay.", content_type="text/plain")

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
