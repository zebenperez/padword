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
from contents.models import ItemInCat
from web.models import Project
from .models import ProjectAvantioUser, ProjectAvaibookUser, ProjectWinhotelUser, ProjectMewsUser, ProjectCloudbedsUser
from .models import ProjectPaytefUser
from .avantio_lib import get_booking_list, get_booking_notif, send_link
from .avaibook_lib import get_accommodation_list, manage_booking_from_webhook, get_booking_list as av_get_booking_list, WEBHOOK_TOKEN
from .winhotel_lib import get_booking_list as wh_get_booking_list, import_item_prices as wh_import_item_prices
from .winhotel_lib import get_booking_new_list as wh_get_booking_new_list, get_booking_day_list as wh_get_booking_day_list
from .winhotel_lib import get_booking_range_list as wh_get_booking_range_list
from .mews_lib import get_booking_list as mw_get_booking_list, cancel_booking_list as mw_cancel_booking_list
from .cloudbeds_lib import get_booking_list as cb_get_booking_list, get_room_list as cb_get_room_list
from .cloudbeds_lib import set_webhooks as cb_set_webhooks, manage_webhook_actions as cb_manage_webhook_actions
from .paytef_lib import get_config as pay_get_config

import json, os, csv, re


'''
    Avantio
'''
def avantio_write_log(result):
    f = open(os.path.join(settings.BASE_DIR, "avantio.log"), "a", encoding='utf-8')
    f.write(result)
    f.close()

@group_required("admins", "projects")
def avantio_get_booking_list(request, project_uuid):
    try:
        booking_list, err = get_booking_list(project_uuid)

        pau = ProjectAvantioUser.objects.filter(project_uuid=project_uuid).first()
        if pau != None and pau.email != "":
            project = get_or_none(Project, project_uuid, "uuid")
            result = "Importación Manual {} {}\n".format(project.name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            result += "-----------------------------------------------------"
            result += render_to_string('avantio/booking-log.html', {'booking_list': booking_list, "error": err})
            subject = "Importación {} {}".format(project.name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            send_email(subject, result, settings.EMAIL_FROM_DEFAULT, [pau.email])
            #send_email(subject, result, "no-reply@padword.es", [pau.email])
            avantio_write_log(result)

        return render(request, 'avantio/booking-list.html', {'booking_list': booking_list, "error": err})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def avantio_get_booking_notif(request, project_uuid):
    try:
        booking_list = get_booking_notif(project_uuid)

        pau = ProjectAvantioUser.objects.filter(project_uuid=project_uuid).first()
        if pau != None and pau.email != "":
            project = get_or_none(Project, project_uuid, "uuid")
            result = "Notificatión Manual {} {}\n".format(project.name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            result += "-----------------------------------------------------"
            result += render_to_string('avantio/booking-log.html', {'booking_list': booking_list})
            avantio_write_log(result)

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

@group_required("admins")
def avantio_log(request):
    f = open(os.path.join(settings.BASE_DIR, "avantio.log"), "r", encoding='utf-8')
    text = f.read()
    try:
        log_list = [f for f in os.listdir(settings.LOGPATH) if re.match(r'.*avantio.*', f)]
    except:
        log_list = []
    return render(request, 'cron-log.html', {'text': text.replace("\n", "<br/>"), 'log_list': log_list})

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
    f.write("\n{} - Recibida reserva de avaibook".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    f.write("\n{}".format(request.headers))

    given_token = request.headers.get("Avaibook-Webhook-Token", "")
    if not compare_digest(given_token, WEBHOOK_TOKEN):
        f.write("\nToken no valido".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        return HttpResponseForbidden(
            "Incorrect token in Avaibook-Webhook-Token header.",
            content_type="text/plain",
        )

    booking = json.loads(request.body)
    f.write("\n{}".format(booking))

    try:
        #pau = get_or_none(ProjectAvaibookUser, settings.AVAIBOOK_ID, "project_uuid")
        pau = get_or_none(ProjectAvaibookUser, booking["owner_id"], "owner")
        err = manage_booking_from_webhook(pau, booking)
        if err != "":
            f.write("\nError Lock: {}".format(err))
        f.write("\nBooking created!")
    except Exception as e:
        f.write("\nError: {}".format(e))

    return HttpResponse("Message received okay.", content_type="text/plain")

@group_required("admins")
def avaibook_log(request):
    f = open(os.path.join(settings.BASE_DIR, "avaibook.log"), "r", encoding='utf-8')
    text = f.read()
    try:
        log_list = [f for f in os.listdir(settings.LOGPATH) if re.match(r'.*avaibook.*', f)]
    except:
        log_list = []
    return render(request, 'cron-log.html', {'text': text.replace("\n", "<br/>"), 'log_list': log_list})

'''
    Winhotel
'''
@group_required("admins", "projects")
def winhotel_get_booking_list(request, project_uuid):
    try:
        pau = get_or_none(ProjectWinhotelUser, project_uuid, "project_uuid")
        #booking_list, err = wh_get_booking_list(pau, "1")
        #booking_list, err = wh_get_booking_new_list(pau, "1")
        booking_list, err = wh_get_booking_range_list(pau, "1")
        return render(request, 'winhotel/booking-list.html', {'booking_list': booking_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def winhotel_get_day_booking_list(request):
    try:
        pwu = get_or_none(ProjectWinhotelUser, request.POST["obj_id"])
        source = request.POST["source"]
        target = request.POST["target"]
        date = request.POST["date"]
        booking_list, err = wh_get_booking_day_list(pwu, "1", source, target, date)
        return render(request, 'winhotel/booking-list.html', {'booking_list': booking_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


@group_required("admins", "projects")
def winhotel_import_items(request, project_uuid):
    updated = []
    not_updated = []
    if request.POST:
        pau = ProjectWinhotelUser.objects.filter(project_uuid=project_uuid).first()
        file = request.FILES['file']
        updated, not_updated = wh_import_item_prices(file, project_uuid, pau.update_all_prices)
    return render(request, 'winhotel/items-import.html', {'project_uuid': project_uuid, 'updated': updated, 'not_updated': not_updated})

@group_required("admins")
def winhotel_log(request):
    f = open(os.path.join(settings.BASE_DIR, "winhotel.log"), "r", encoding='utf-8')
    text = f.read()
    try:
        log_list = [f for f in os.listdir(settings.LOGPATH) if re.match(r'.*winhotel.*', f)]
    except:
        log_list = []
    return render(request, 'cron-log.html', {'text': text.replace("\n", "<br/>"), 'log_list': log_list})

#    updated = []
#    not_updated = []
#    if request.POST:
#        file = request.FILES['file']
#        decoded_file = file.read().decode('latin-1').splitlines()
#        for line in decoded_file:
#            update = False
#            dic_line = line.split(";")
#            #print("{} - {}".format(dic_line[3], dic_line[5]))
#            try:
#                ic_list = ItemInCat.objects.filter(category__project_uuid = project_uuid, item__ext_id = int(dic_line[3]))
#                for ic in ic_list:
#                    ic.item.price = float(dic_line[5].replace(",", "."))
#                    ic.item.save()
#                    update = True
#            except Exception as e:
#                print(e)
#            if update:
#                updated.append(dic_line)
#            else:
#                not_updated.append(dic_line)
#    return render(request, 'winhotel/items-import.html', {'project_uuid': project_uuid, 'updated': updated, 'not_updated': not_updated})

'''
    Mews
'''
@group_required("admins", "projects")
def mews_get_booking_list(request, project_uuid):
    try:
        pmu = get_or_none(ProjectMewsUser, project_uuid, "project_uuid")
        booking_list = mw_get_booking_list(pmu)
        return render(request, 'mews/booking-list.html', {'booking_list': booking_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def mews_cancel_booking_list(request, project_uuid):
    try:
        pmu = get_or_none(ProjectMewsUser, project_uuid, "project_uuid")
        booking_list = mw_cancel_booking_list(pmu)
        return render(request, 'mews/booking-list.html', {'booking_list': booking_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

'''
    Cloudbeds
'''
@group_required("admins", "projects")
def cloudbeds_get_booking_list(request, project_uuid):
    try:
        pmu = get_or_none(ProjectCloudbedsUser, project_uuid, "project_uuid")
        booking_list = cb_get_booking_list(pmu)
        return render(request, 'cloudbeds/booking-list.html', {'booking_list': booking_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def cloudbeds_get_room_list(request, project_uuid):
    try:
        pau = get_or_none(ProjectCloudbedsUser, project_uuid, "project_uuid")
        item_list = cb_get_room_list(pau)
        return render(request, 'cloudbeds/room-list.html', {'item_list': item_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def cloudbeds_set_webhooks(request):
    try:
        pcu = get_or_none(ProjectCloudbedsUser, project_uuid, "project_uuid")
        if pcu.property_id == "":
            return HttpResponse("Property ID can not be empty!")
        result = cb_set_webhooks(pcu)
        return HttpResponse(result)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@csrf_exempt
@require_POST
def cloudbeds_webhook(request):
    f = open(os.path.join(settings.BASE_DIR, "cloudbeds.log"), "a", encoding='utf-8')
    f.write("\n---------------------------------------")
    f.write("\n{} - Evento de cloudbeds".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    #f.write("\n{}".format(request.headers))
    f.write("\n{}".format(request.body))

    try:
        booking = json.loads(request.body)
        pcu = None
        if "propertyId_str" in booking:
            pcu = get_or_none(ProjectCloudbedsUser, booking["propertyId_str"], "property_id")
        elif "propertyID_str" in booking:
            pcu = get_or_none(ProjectCloudbedsUser, booking["propertyID_str"], "property_id")
        if pcu == None:
            if "propertyId_str" in booking:
                f.write("\nError: Propiedad {} no encontrada".format(booking["propertyId_str"]))
            elif "propertyID_str" in booking:
                f.write("\nError: Propiedad {} no encontrada".format(booking["propertyID_str"]))
            else:
                f.write("\nError: Propiedad no encontrada")

        if pcu != None and pcu.project != None:
            f.write("\n PROYECTO: {}".format(pcu.project.name))
        msg = cb_manage_webhook_actions(pcu, booking)
        f.write(msg)
    except Exception as e:
        f.write("\nError: {}".format(e))

    return HttpResponse("OK", content_type="text/plain")

@group_required("admins")
def cloudbeds_log(request):
    f = open(os.path.join(settings.BASE_DIR, "cloudbeds.log"), "r", encoding='utf-8')
    text = f.read()
    try:
        log_list = [f for f in os.listdir(settings.LOGPATH) if re.match(r'.*cloudbeds.*', f)]
    except:
        log_list = []
    return render(request, 'cron-log.html', {'text': text.replace("\n", "<br/>"), 'log_list': log_list})


'''
    Paytef
'''
@group_required("admins", "projects")
def paytef_get_config(request, project_uuid):
    try:
        ppu = get_or_none(ProjectPaytefUser, project_uuid, "project_uuid")
        config = pay_get_config(ppu)
        return render(request, 'paytef/config.html', {'config': config})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

'''
    Zkteco
'''
@csrf_exempt
#@require_POST
def zkteco_webhook(request):
    f = open(os.path.join(settings.BASE_DIR, "zkteco.log"), "a", encoding='utf-8')
    f.write("\n---------------------------------------")
    f.write("\n{} - Evento de zkteco".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    #f.write("\n{}".format(request.headers))
    f.write("\nGET: {}".format(request.GET))
    f.write("\nPOST: {}".format(request.POST))
    f.write("\nBODY: {}".format(request.body))
    return HttpResponse("OK", content_type="text/plain")


'''
    ACCESS CONTROL
'''
def access_control(request, project, card):
    f = open(os.path.join(settings.BASE_DIR, "access_control.log"), "a", encoding='utf-8')
    f.write("\n---------------------------------------")
    f.write("\n{} - Recibida lectura de tarjeta".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    try:
        pr = get_or_none(Project, project, "uuid")
        if pr == None:
            f.write("\nError: {}".format(e))
        else:
            f.write("\nProject: {} - Card: {}".format(pr.name, card))
    except Exception as e:
        f.write("\nError: {}".format(e))
    return HttpResponse("")


'''
    Cron Logs
'''
@group_required("admins")
def cron_log(request):
    f = open(os.path.join(settings.BASE_DIR, "cron.log"), "r", encoding='utf-8')
    text = f.read()
    try:
        log_list = [f for f in os.listdir(settings.LOGPATH) if re.match(r'.*cron.*', f)]
    except:
        log_list = []
    return render(request, 'cron-log.html', {'text': text.replace("\n", "<br/>"), 'log_list': log_list})

@group_required("admins")
def test_email(request):
    send_email("test", "test", settings.EMAIL_FROM_DEFAULT, ["zebenperez@gmail.com", "soporte@padword.es"])
    return HttpResponse("Ok")
