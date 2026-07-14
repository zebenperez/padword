from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _ 
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from datetime import datetime
from secrets import compare_digest

from padword.commons import show_exc, get_or_none, get_param, get_random_digits, reverse_cardkey
from padword.email_lib import send_email
from padword.decorators import group_required
from contents.models import ItemInCat
from web.models import Project, ProjectUser, ProjectAux
from web.models_lock import LockRecord
from guest.models import Guest
from guest.wristband_models import WristbandAccessZone, Wristband, WristbandAccessZoneGuest
from .models import ProjectAvantioUser, ProjectAvaibookUser, ProjectWinhotelUser, ProjectMewsUser, ProjectCloudbedsUser
from .models import ProjectPaytefUser, ProjectZktecoUser, ProjectRoomraccoonUser, ProjectOctorateUser
from .avantio_lib import get_booking_list, get_booking_notif, send_link
from .avaibook_lib import get_accommodation_list, manage_booking_from_webhook, get_booking_list as av_get_booking_list, WEBHOOK_TOKEN
from .winhotel_lib import get_booking_list as wh_get_booking_list, import_item_prices as wh_import_item_prices
from .winhotel_lib import get_booking_new_list as wh_get_booking_new_list, get_booking_day_list as wh_get_booking_day_list
from .winhotel_lib import get_booking_range_list as wh_get_booking_range_list, send_liq as wh_send_liq
from .mews_lib import get_booking_list as mw_get_booking_list, cancel_booking_list as mw_cancel_booking_list
from .mews_lib import get_room_list as mw_get_room_list
from .cloudbeds_lib import get_booking_list as cb_get_booking_list, get_room_list as cb_get_room_list
from .cloudbeds_lib import set_webhooks as cb_set_webhooks, manage_webhook_actions as cb_manage_webhook_actions
from .octorate_lib import get_booking_list as oc_get_booking_list, get_room_list as oc_get_room_list
from .paytef_lib import get_config as pay_get_config, get_status as pay_get_status, start_trans as pay_start_trans, get_token as pay_get_token
from .zkteco_lib import add_person as zk_add_person
from .roomraccoon import roomraccoon_get_soap_response, roomraccoon_get_soap_header, roomraccoon_get_soap_body, roomraccoon_parse_soap_reservation, roomraccoon_manage_booking

import json, os, csv, re, threading 


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

def winhotel_get_total_by_source(date, pt, i_list):
    from bookings.models import FormInstance
    from contents.models import ShoppingCart
    from django.db.models import Sum

    d = date.strftime("%Y-%m-%d")
    ini = datetime.strptime(f'{d} 00:00:00', "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(f'{d} 23:59:59', "%Y-%m-%d %H:%M:%S")
    fi_list = FormInstance.objects.filter(date__range=(ini, end), payment_type__code=pt, status_list__isnull=False).values_list('id', flat=True)
    #print("--A--")
    #print(pt)
    #print(date)
    #print(fi_list)
    amount = ShoppingCart.objects.filter(form_instance_id__in=fi_list, item__ext_id__in=i_list).aggregate(total_price_sum=Sum('total_price'))
    return amount['total_price_sum'] if amount['total_price_sum'] != None else 0

def winhotel_liq_params(name, code, source, cash_code, total):
    source_document = f'Punto de venta {name}'
    date = datetime.today().strftime("%Y-%m-%d")
    _send_charge_params = {
        "ExternalCharge": {
            "CreditContact": {
                "RoomCode": "",
                "ContactName": name ,
                "ContactId": code,
                "HasCredit": "true",
            },
            "Source": source,
            "SourceDocument": source_document,
            "Date": date,
            "TotalAmount": total,
            "CashCode": cash_code
        }
    }
    return _send_charge_params

@group_required("admins", "projects")
def winhotel_send_liq(request, project_uuid, pos_code):
    from django.utils import timezone 
    from contents.models import PosCodeItem, PointOfSale

    res2 = []
    pwu = ProjectWinhotelUser.objects.filter(project_uuid=project_uuid).first()
    pos = get_or_none(PointOfSale, pos_code, "ext_code")
    pci_list = PosCodeItem.objects.filter(project_uuid=project_uuid, pos=pos_code)
    sources = {}
    for item in pci_list:
        if item.code not in sources:
            sources[item.code] = {"name": item.name, "items":[]}
        sources[item.code]["items"].append(item.item_id)
    total = 0
    total_cash = 0
    total_card = 0
    for key in sources.keys():
        ta_cash = winhotel_get_total_by_source(timezone.localdate(), "01", sources[key]['items'])
        ta_cash_disc = winhotel_get_total_by_source(timezone.localdate(), "0401", sources[key]['items'])
        ta_card = winhotel_get_total_by_source(timezone.localdate(), "02", sources[key]['items'])
        ta_card_disc = winhotel_get_total_by_source(timezone.localdate(), "0402", sources[key]['items'])
        total_a = ta_cash + ta_card + ta_cash_disc + ta_card_disc

        res2.append(winhotel_liq_params(pos.name, pos.contact_code, f'LIQ-{key}', "COBROS", total_a))

        total_cash += ta_cash + ta_cash_disc 
        total_card += ta_card + ta_card_disc
        total += total_cash + total_card 

    res2.append(winhotel_liq_params(pos.name, pos.contact_code, "TOTAL", "---", total))
    res2.append(winhotel_liq_params(pos.name, pos.contact_code, "TOTAL CASH", "CASH", total_cash))
    res2.append(winhotel_liq_params(pos.name, pos.contact_code, "TOTAL CARD", "CARD", total_card))
    return HttpResponse( "<pre>{}</pre>".format( json.dumps(res2, indent=4, ensure_ascii=False)))

#def winhotel_liq_params(name, code, source, cash_code, total):
#    res = f"<br/>"
#    source_document = f'Punto de venta {name}'
#    date = datetime.today().strftime("%Y-%m-%d")
#    res += f"<br/> contact_name = {name}"
#    res += f"<br/> contact_id = {code}"
#    res += f"<br/> source = {source}"
#    res += f"<br/> source_document = Punto de venta {source_document}"
#    res += f"<br/> date = {date}"
#    res += f"<br/> total_amount = {total}"
#    res += f"<br/> cash_code = {cash_code}"
#    #print(f'contact_name = {name}')
#    #print(f'contact_id = {code}')
#    #print(f'source = {source}')
#    #print(f'source_document = Punto de venta {source_document}')
#    #print(f'date = {date}')
#    #print(f'total_amount = {total}')
#    #print(f'cash_code = {cash_code}')
#    _send_charge_params = {
#        "ExternalCharge": {
#            "CreditContact": {
#                "RoomCode": "",
#                "ContactName": name ,
#                "ContactId": code,
#                "HasCredit": "true",
#            },
#            "Source": source,
#            "SourceDocument": source_document,
#            "Date": date,
#            "TotalAmount": total,
#            "CashCode": cash_code
#        }
#    }
#    res = f"{_send_charge_params}"
#    return json.dumps(res, indent=4, ensure_ascii=False)
#    return res
#
#
#@group_required("admins", "projects")
#def winhotel_send_liq(request, project_uuid, pos_code):
#    from django.utils import timezone 
#    from contents.models import PosCodeItem, PointOfSale
#
#    res = ""
#    res2 = []
#    pwu = ProjectWinhotelUser.objects.filter(project_uuid=project_uuid).first()
#    pos = get_or_none(PointOfSale, pos_code, "ext_code")
#    #print(pwu)
#    res += f"<br/> {pwu.project_uuid}"
#    #print(pos_code)
#    res += f"<br/> {pos_code}"
#    pci_list = PosCodeItem.objects.filter(project_uuid=project_uuid, pos=pos_code)
#    #print(len(pci_list))
#    sources = {}
#    for item in pci_list:
#        if item.code not in sources:
#            sources[item.code] = {"name": item.name, "items":[]}
#        sources[item.code]["items"].append(item.item_id)
#    total = 0
#    total_cash = 0
#    total_card = 0
#    for key in sources.keys():
#        ta_cash = winhotel_get_total_by_source(timezone.localdate(), "01", sources[key]['items'])
#        ta_cash_disc = winhotel_get_total_by_source(timezone.localdate(), "0401", sources[key]['items'])
#        ta_card = winhotel_get_total_by_source(timezone.localdate(), "02", sources[key]['items'])
#        ta_card_disc = winhotel_get_total_by_source(timezone.localdate(), "0402", sources[key]['items'])
#        total_a = ta_cash + ta_card + ta_cash_disc + ta_card_disc
#
#        res += f"<hr/>"
#        #print(key)
#        res += f"<br/> {key}"
#        #print(sources[key])
#        res += f"<br/> {sources[key]}"
#        res += winhotel_liq_params(pos.name, pos.contact_code, f'LIQ-{key}', "COBROS", total_a)
#        res2.append(winhotel_liq_params(pos.name, pos.contact_code, f'LIQ-{key}', "COBROS", total_a))
#
#        total_cash += ta_cash + ta_cash_disc 
#        total_card += ta_card + ta_card_disc
#        total += total_cash + total_card 
#
##        total_amount = winhotel_get_total_by_source(timezone.localdate(), "01", sources[key]['items'])
##        total_amount_disc = winhotel_get_total_by_source(timezone.localdate(), "0401", sources[key]['items'])
##        total_a = total_amount + total_amount_disc
##        cash_code = "CASH"
##        print(f'total_amount = {total_a}')
##        res += f"<br/> total_amount = {total_a}"
##        print(f'cash_code = {cash_code}')
##        res += f"<br/> cash_code = {cash_code}"
##
##        total_amount = winhotel_get_total_by_source(timezone.localdate(), "02", sources[key]['items'])
##        total_amount_disc = winhotel_get_total_by_source(timezone.localdate(), "0402", sources[key]['items'])
##        total_a = total_amount + total_amount_disc
##        cash_code = "CARD"
##        print(f'total_amount = {total_a}')
##        res += f"<br/> total_amount = {total_a}"
##        print(f'cash_code = {cash_code}')
##        res += f"<br/> cash_code = {cash_code}"
#
#        #wh_send_liq(pwu, contact_name, contact_id, source, source_document, date, total_amount, cash_code)
#
#    res += f"<hr/>"
#    res += winhotel_liq_params(pos.name, pos.contact_code, "TOTAL", "---", total)
#    res += f"<hr/>"
#    res += winhotel_liq_params(pos.name, pos.contact_code, "TOTAL CASH", "CASH", total_cash)
#    res += f"<hr/>"
#    res += winhotel_liq_params(pos.name, pos.contact_code, "TOTAL CARD", "CARD", total_card)
#    res2.append(winhotel_liq_params(pos.name, pos.contact_code, "TOTAL", "---", total))
#    res2.append(winhotel_liq_params(pos.name, pos.contact_code, "TOTAL CASH", "CASH", total_cash))
#    res2.append(winhotel_liq_params(pos.name, pos.contact_code, "TOTAL CARD", "CARD", total_card))
#    return HttpResponse(res2)
#

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

@group_required("admins", "projects")
def mews_get_room_list(request, project_uuid):
    try:
        pmu = get_or_none(ProjectMewsUser, project_uuid, "project_uuid")
        room_list = mw_get_room_list(pmu)
        return render(request, 'mews/room-list.html', {'item_list': room_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


@group_required("admins", "projects")
def mews_email_template(request, project_uuid, guest_uuid):
    from .mews_lib import send_email_code

    project = get_or_none(Project, project_uuid, "uuid")
    #guest = Guest.objects.filter(project_id=project_uuid).first()
    guest = get_or_none(Guest, guest_uuid, "UUID")
    pmu = ProjectMewsUser.objects.filter(project_uuid=project_uuid).first()
    email = send_email_code(guest, "1234", pmu)
    return HttpResponse(email)
    #lang = guest.language or "es"
    #translation.activate(lang)
    #return render(request, 'mews/email_template.html', {'guest': guest, 'project': project, 'pmu': pmu})

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

@group_required("admins", "projects")
def cloudbeds_remove_webhooks(request):
    try:
        pcu = get_or_none(ProjectCloudbedsUser, project_uuid, "project_uuid")
        if pcu.property_id == "":
            return HttpResponse("Property ID can not be empty!")
        result = cb_remove_webhooks(pcu)
        return HttpResponse(result)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


def cloudbeds_manage_webhook(pcu, booking, f):
    msg = cb_manage_webhook_actions(pcu, booking)
    f.write(msg)

@csrf_exempt
@require_POST
def cloudbeds_webhook(request):
    #import random
    #import time

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

        #p = Project.objects.filter(uuid=pcu.project_uuid).first()
        #if pcu != None and p != None:
        #    f.write("\n PROYECTO: {}".format(p.name))

        #if booking["event"] != "reservation/created":
        #    time.sleep(random.randint(8, 12))

        t = threading.Thread(target=cloudbeds_manage_webhook, args=[pcu, booking, f], daemon=True)
        t.start()
        #msg = cb_manage_webhook_actions(pcu, booking)
        #f.write(msg)
    except Exception as e:
        f.write("\nError: {}".format(e))

    return JsonResponse({"status": "OK"}, status=200)
    #return HttpResponse("OK", content_type="text/plain")

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
    Octorate
'''
@group_required("admins", "projects")
def octorate_get_booking_list(request, project_uuid):
    try:
        pou = get_or_none(ProjectOctorateUser, project_uuid, "project_uuid")
        booking_list = oc_get_booking_list(pou)
        return render(request, 'octorate/booking-list.html', {'booking_list': booking_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def octorate_get_room_list(request, project_uuid):
    try:
        pau = get_or_none(ProjectOctorateUser, project_uuid, "project_uuid")
        item_list = oc_get_room_list(pau)
        return render(request, 'octorate/room-list.html', {'item_list': item_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@csrf_exempt  
def octorate_update_token(request):
    f = open(os.path.join(settings.BASE_DIR, "octorate.log"), "a", encoding='utf-8')
    f.write("\n---------------------------------------")
    f.write("\n{} - Evento de octorate".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    #f.write(str(request.GET))
    f.write(str(request.POST))
    return HttpResponse("OK")

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

@group_required("admins", "projects")
def paytef_pinpad_status(request, project_uuid):
    try:
        ppu = get_or_none(ProjectPaytefUser, project_uuid, "project_uuid")
        config = pay_get_status(ppu)
        return render(request, 'paytef/config.html', {'config': config})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def paytef_test_transfer(request, project_uuid):
    try:
        ppu = get_or_none(ProjectPaytefUser, project_uuid, "project_uuid")
        is_ok, config = pay_start_trans(ppu)
        return render(request, 'paytef/transfer.html', {'is_ok': is_ok, 'config': config})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def paytef_get_token(request, project_uuid):
    try:
        ppu = get_or_none(ProjectPaytefUser, project_uuid, "project_uuid")
        config = pay_get_token(ppu)
        return render(request, 'paytef/config.html', {'config': config})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


'''
    Zkteco
'''
def get_person_dic(guest, pzu, code, levels):
    pin_aux = code[-7:]
    pin = "1{}".format(pin_aux) if pin_aux.startswith("0") else pin_aux
    return {
        "accStartTime": guest.check_in.strftime("%Y-%m-%d %H:%M:%S"), #"2025-07-14 12:00:00",
        "accEndTime": guest.check_out.strftime("%Y-%m-%d %H:%M:%S"), #"2025-07-14 12:00:00",
        "accLevelIds": levels,
        #"accLevelIds": zone.code,
        "deptCode": pzu.dep,
        "cardNo": str(reverse_cardkey(code)),
        #"cardNo": str(code),
        "lastName": guest.surname,
        "name": guest.name,
        "pin": pin
        #"pin": code[-7:]
        #"pin": get_random_digits(6) #"202507"                    
    }
 
def send_person_code(pzu, guest, code):
    res = ""
    level = ""
    zone_list = WristbandAccessZoneGuest.objects.filter(guest=guest, code=code)
    if len(zone_list) == 0:
        dic = get_person_dic(guest, pzu, code, "")
    else:
        for ac in zone_list:
            level = "{},{}".format(level, ac.zone.code) if level != "" else ac.zone.code
        dic = get_person_dic(guest, pzu, code, level)
    #print("--1--")
    #print(code)
    #print(dic)
    res += json.dumps(dic)
    res += "<br/>"
    res += zk_add_person(pzu, dic)
    res += "<br/><br/>"
    return res

@group_required("admins", "projects")
def zkteco_add_persons(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        pzu = get_or_none(ProjectZktecoUser, guest.project_id, "project_uuid")
        redirect = get_param(request.GET, "redirect")
        res = "Guest: {}".format(guest)
        res += "<br/><br/>"

        for b in guest.bands.all():
            res += send_person_code(pzu, guest, b.code)
        for c in guest.cards_for_access(): 
            res += send_person_code(pzu, guest, c.code)

        return render(request, 'zkteco/result.html', {'params': "", 'res': res, 'redirect': redirect})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def zkteco_add_person_band(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        pzu = get_or_none(ProjectZktecoUser, guest.project_id, "project_uuid")
        code = get_param(request.GET, "band")
        res = "Guest: {}".format(guest)
        res += "<br/><br/>"

        res += send_person_code(pzu, guest, code)

        return render(request, 'zkteco/result.html', {'params': "", 'res': res})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

#@group_required("admins", "projects")
#def zkteco_add_person(request):
#    try:
#        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
#        zone = get_or_none(WristbandAccessZone, get_param(request.GET, "zone"))
#        wband = get_param(request.GET, "band")
#        pzu = get_or_none(ProjectZktecoUser, guest.project_id, "project_uuid")
#        res = "Guest: {} --- Zone: {}".format(guest, zone)
#
#        dic = get_person_dic(guest, pzu, wband, zone.code, "")
#        res = zk_add_person(pzu, dic)
#
#        return render(request, 'zkteco/result.html', {'params': dic, 'res': res})
#    except Exception as e:
#        print(e)
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})
#
#@csrf_exempt
##@require_POST
#def zkteco_webhook(request):
#    f = open(os.path.join(settings.BASE_DIR, "zkteco.log"), "a", encoding='utf-8')
#    f.write("\n---------------------------------------")
#    f.write("\n{} - Evento de zkteco".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
#    #f.write("\n{}".format(request.headers))
#    f.write("\nGET: {}".format(request.GET))
#    f.write("\nPOST: {}".format(request.POST))
#    f.write("\nBODY: {}".format(request.body))
#    return HttpResponse("OK", content_type="text/plain")
#

'''
    ROOMRACCOON
'''
from django.contrib.auth import authenticate

def roomraccoon_write_log(xml_body):
    f = open(os.path.join(settings.BASE_DIR, "roomraccoon.log"), "a", encoding='utf-8')
    f.write("\n---------------------------------------")
    f.write("\n{} - Recibida reserva de roomraccoon".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    f.write("\n{}".format(xml_body))

@csrf_exempt  # SOAP no maneja CSRF tokens
def roomraccoon_get_booking(request):
    if request.method != "POST":
        return HttpResponse("Método no permitido", status=405)

#    auth_header = request.META.get("HTTP_AUTHORIZATION")
#    if not auth_header or not auth_header.startswith("Basic "):
#        response = HttpResponse("No autorizado", status=401)
#        response["WWW-Authenticate"] = 'Basic realm="SOAP API"'
#        return response
#
#    try:
#        encoded = auth_header.split(" ")[1]
#        decoded = base64.b64decode(encoded).decode("utf-8")
#        username, password = decoded.split(":")
#    except Exception:
#        return HttpResponse("Credenciales inválidas", status=400)
#
#    user = authenticate(username=username, password=password)
#    if user == None:
#        response = HttpResponse("No autorizado", status=401)
#        response["WWW-Authenticate"] = 'Basic realm="SOAP API"'
#        return response

    f = open(os.path.join(settings.BASE_DIR, "roomraccoon.log"), "a", encoding='utf-8')
    f.write("\n[LOG]: ENTRA")

    roomraccoon_write_log(request.body.decode("utf-8"))
    auth_header = roomraccoon_get_soap_header(request.body.decode("utf-8"))

    f.write("\n[LOG]: {}".format(auth_header))
    if auth_header == None:
        return HttpResponse("Credenciales inválidas", status=400)

    f.write("\n[LOG]: VALIDACION")
    user = authenticate(username=auth_header["username"], password=auth_header["password"])
    if user == None:
        response = HttpResponse("No autorizado", status=401)
        response["WWW-Authenticate"] = 'Basic realm="SOAP API"'
        return response

    try:
        f.write("\n[LOG]: CONTENIDO")
        #contenido = roomraccoon_get_soap_body(request.body.decode("utf-8"))
        #pu = get_or_none(ProjectUser, user.username, "username")
        #pru = get_or_none(ProjectRoomraccoonUser, pu.project_uuid, "project_uuid")
        content = roomraccoon_parse_soap_reservation(request.body.decode("utf-8"))
        f.write("\n[LOG]: PROYECTO (HOTEL): {}".format(content["hotel_code"]))
        #print(content)
        pru = get_or_none(ProjectRoomraccoonUser, content["hotel_code"], "hotel")
        f.write("\n[LOG]: PROYECTO: {}".format(pru.project_uuid))
        err = roomraccoon_manage_booking(pru, content, f)
        soap_response = roomraccoon_get_soap_response() # Resuesta SOAP
        return HttpResponse(soap_response, content_type="text/xml")
    except Exception as e:
        f.write("\n[LOG]: ERROR: {}".format(str(e)))
        print("❌ Error procesando SOAP:", e)
        return HttpResponse("Error procesando SOAP", status=400)

@group_required("admins")
def roomraccoon_log(request):
    f = open(os.path.join(settings.BASE_DIR, "roomraccoon.log"), "r", encoding='utf-8')
    text = f.read()
    try:
        log_list = [f for f in os.listdir(settings.LOGPATH) if re.match(r'.*roomraccoon.*', f)]
    except:
        log_list = []
    return render(request, 'cron-log.html', {'text': text.replace("\n", "<br/>"), 'log_list': log_list})

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
    TTLOCK
'''
@csrf_exempt
def lock_record_callback(request):
    if request.method != "POST":
        return HttpResponse("method not allowed", status=405)

    try:
        notify_type = get_param(request.POST, "notifyType")
        lock_id = get_param(request.POST, "lockId")
        lock_mac = get_param(request.POST, "lockMac")

        # Viene como string JSON
        records_str = request.POST.get("records", "[]")
        records = json.loads(records_str)

        #print(f"Lock callback recibido: notifyType={notify_type} lockId={lock_id} lockMac={lock_mac}")

        for record in records:
            record_type =get_param(record, "recordType")
            success = get_param(record, "success")
            username = get_param(record, "username")
            keyboard_pwd = get_param(record, "keyboardPwd") 
            electric_quantity = get_param(record, "electricQuantity")

            lock_date_ms = get_param(record, "lockDate")
            server_date_ms = get_param(record, "serverDate")

            lock_date = (datetime.fromtimestamp(lock_date_ms / 1000) if lock_date_ms else None)

            server_date = (datetime.fromtimestamp(server_date_ms / 1000) if server_date_ms else None)

            #print(f"Record: record_type={record_type} success={success} username={username} keyboard_pwd={keyboard_pwd} electric_quantity={electric_quantity} lock_date={lock_date} server_date={server_date}")
            LockRecord.objects.create(
                notify_type = notify_type, 
                uuid = lock_id, 
                mac = lock_mac,
                record_type = record_type,
                success = success,
                username = username, 
                keyboard_pwd = keyboard_pwd, 
                electric_quantity = electric_quantity,
                lock_date = lock_date, 
                server_date = server_date
            )
        # El proveedor exige responder exactamente "success"
        return HttpResponse( "success", content_type="text/plain", status=200,)
    except Exception as e:
        print(e)
        return HttpResponse("error", status=500)

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
