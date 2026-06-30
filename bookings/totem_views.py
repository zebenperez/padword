from django.contrib import auth
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, reverse_cardkey
from web.models import Project
from bookings.models import Form, FormInstance
from contents.models import ShoppingCart, PaymentType
from guest.models import Guest
from guest.wristband_models import Wristband, WristbandBalance, WristbandBackup, WristbandBackupBalance
from guest.wristband_lib import close_band_by_regime_and_soft_remove
from connector.models import ProjectPaytefUser, ProjectCaldeaUser
from connector.caldea_lib import send_payment as caldea_send_payment
from .tpv_paytef_lib import manage_transaction
from .common_lib import user_in_group

from django.conf import settings

import datetime, time
import logging
logger = logging.getLogger(__name__)


'''
    Bookings client methods
'''
def check_user(user):
    if not user.is_authenticated:
        return False
    if not user_in_group(user, "waiters"):
        return False
    return True

def totem_access(request, project_uuid, code=""):
    project = get_or_none(Project, project_uuid, "uuid")

    context = {'project_uuid': project.uuid}
    #if check_user(request.user):
    #    next_url = reverse("totem-index", kwargs = context)
    #else:
    #    auth.logout(request)
    #    next_url = reverse("totem-start")
    next_url = reverse("totem-start")

    form = Form.objects.filter(form_type__code="totem", form_type__project_uuid=project.uuid).first()
    context["next_url"] = next_url
    context["form"] = form
    context["cat"] = form.get_category
    context["code"] = code
    if code != "":
        request.session["code"] = code
    return render(request, 'bookings/totem/totem-welcome.html', context)

def totem_start(request):
    return render(request, "bookings/totem/check-band.html", {'project_uuid': request.GET["project_uuid"], 'error': ''})

def totem_check_band(request):
    try:
        project = get_or_none(Project, get_param(request.GET, "project"), "uuid")
        val = get_param(request.GET, "value", "")
        band = Wristband.get_active_by_project(project, reverse_cardkey(val))
        tcod = request.session["code"] if "code" in request.session else ""
        band_err = ""
        #print(f"--> Lectura de pulsera: {val}")
        #print(f"--> Pulsera: {band}")
        if band == None:
            band_err = _("¡Pulsera no encontrada!")
        elif band.guest == None:
            band_err = _("¡Pulsera no asignada!")
        #elif band.is_close:
        #    band_err = _("¡Esta pulsera ya ha sido cerrada!")
        else:
            gr = band.guest.regimes.first()
            regime = gr.regime if gr != None else None

        form = Form.get_totem(project.uuid)
        context = {'band':band, 'band_err': band_err, 'form': form, 'project': project, 'tcod': tcod}
        return render(request, "bookings/totem/view-band.html", context)
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

#def add_pay_to_band(band, amount):
#    desc += "Pago realizado a través del Totem de ".format(url, fi.id, fi.get_index)
#    WristbandBalance.objects.create(amount=amount, desc=desc, wristband=band)
    #WristbandBalance.objects.create(amount=(get_float(fi.amount)*-1), desc=desc, wristband=band)

def totem_pay(request):
    project = get_or_none(Project, request.GET["project"], "uuid")
    tcod = request.session["code"] if "code" in request.session else ""

    band = get_or_none(Wristband, request.GET["obj_id"])
    if band == None:
        context = {'err': _('Pulsera no encontrada'), 'project': project, 'tcod': tcod}
        return render(request, "bookings/totem/payment-return.html", context)

    ppu = ProjectPaytefUser.objects.filter(project_uuid=project.uuid).first()
    if ppu == None or ppu.tcod == "":
        context = {'err': _('Datafono no encontrado'), 'project': project, 'tcod': tcod}
        return render(request, "bookings/totem/payment-return.html", context)

    total = band.balance
    try:
        #print("--1--")
        payment_ok = manage_transaction(project, -1 * total, "Ticket: {}".format(band.id), tcod)
        if not payment_ok:
            context = {'err': _('Error procesando el pago'), 'project': project, 'tcod': tcod}
            return render(request, "bookings/totem/payment-return.html", context)
    except Exception as e:
        print(e)
        context = {'err': _('Error procesando el pago'), 'project': project, 'tcod': tcod}
        return render(request, "bookings/totem/payment-return.html", context)

    band_code = band.code
    regime = band.guest.regime.code if band.guest != None and band.guest.regime != None else ""
    tickets = get_ticket_ids(band)

    desc = f'Totem (code: {tcod}): liquidación de importe pendiente'
    band.reset_balance(desc)            #Se pone el balance a 0 con cargo
    obj = band.make_new_close()         #Se cierra la pulsera
    Wristband.reset_band(band)          #Se le reasigna vacía al huésped
    band_close = obj.id if obj != None else "" #Se pasa la copia para recuperar luego los balances

    try:
        #print("--2--")
        update_tickets_payment(tickets)
        send_caldea_payment(project, band_code, regime, tickets, (-1 * total))
    except Exception as e:
        print(e)
        #return render(request, "bookings/totem/payment-return.html", {'err': _('Error enviando el pago'), 'project': project})

    context = {'err': '', 'project': project, 'band': band.code, 'total': total, 'band_close': band_close, 'tcod': tcod}
    return render(request, "bookings/totem/payment-return.html", context)

def totem_view_ticket(request):
    #import re
        #match = re.search(r"data-obj_id='(\d+)'", band.desc)
        #fi_id = match.group(1) if match else None

        #fi = FormInstance.objects.get(pk = fi_id)
    try:
        band = get_or_none(WristbandBalance, get_param(request.GET, "obj_id"))
        fi = FormInstance.objects.get(pk = band.ticket_id)
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk)
        context = {'fi': fi, 'index': "0", 'project_uuid': fi.form.project.uuid, 'items':items}
        return render(request, 'bookings/totem/view-ticket.html', context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

def totem_print_pay(request):
    try:
        project = get_or_none(Project, get_param(request.GET, "project_uuid"), "uuid")
        band_close = get_or_none(WristbandBackup, get_param(request.GET, "band_close"))
        band = get_param(request.GET, "band")
        total = get_param(request.GET, "total")
        tcod = request.session["code"] if "code" in request.session else ""

        now = datetime.datetime.now()
        balances = band_close.balances.all()
        #b = Wristband.objects.filter(code=band).first()
        #balances = b.balances.all()
        pcu = ProjectCaldeaUser.objects.filter(project_uuid=project.uuid).first()
        context = {'project': project, 'band': band, 'total': total, 'date': now, 'balances': balances, 'pcu': pcu, 'tcod': tcod}
        return render(request, 'bookings/totem/print-pay.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-print-ticket] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

'''
    COMMONS
'''
def get_ticket_ids(band):
    ticket_ids = []
    for item in band.balances.all():
        ticket_id = item.ticket_id
        if ticket_id != "":
            ticket_ids.append(ticket_id)
    return ticket_ids
 
def update_tickets_payment(tickets):
    try:
        pt = PaymentType.objects.filter(code="09").first() #Pago en totem
        if pt != None:
            for ticket in tickets:
                fi = FormInstance.objects.get(pk = ticket)
                fi.payment_type = pt
                fi.save()
    except Exception as e:
        print(e)

def send_caldea_payment(project, band_code, regime, tickets, total):
    pcu = ProjectCaldeaUser.objects.filter(project_uuid=project.uuid).first()
    if pcu != None and pcu.client_id != "":
        caldea_send_payment(pcu, reverse_cardkey(band_code), regime, tickets, total)


