from django.contrib import auth
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, reverse_cardkey
from web.models import Project
from bookings.models import Form, FormInstance
from contents.models import ShoppingCart
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
        project = get_or_none(Project, request.GET["project"], "uuid")
        val = get_param(request.GET, "value", "")
        band = Wristband.get_active_by_project(project, reverse_cardkey(val))
        band_err = ""
        if band == None:
            band_err = _("¡Pulsera no encontrada!")
        elif band.guest == None:
            band_err = _("¡Pulsera no asignada!")
        elif band.is_close:
            band_err = _("¡Esta pulsera ya ha sido cerrada!")
        else:
            gr = band.guest.regimes.first()
            regime = gr.regime if gr != None else None

        form = Form.get_totem(project.uuid)
        return render(request, "bookings/totem/view-band.html", {'band':band, 'band_err': band_err, 'form': form, 'project': project})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

def add_pay_to_band(band, amount):
    desc += "Pago realizado a través del Totem de ".format(url, fi.id, fi.get_index)
    WristbandBalance.objects.create(amount=amount, desc=desc, wristband=band)
    #WristbandBalance.objects.create(amount=(get_float(fi.amount)*-1), desc=desc, wristband=band)

def totem_pay(request):
    project = get_or_none(Project, request.GET["project"], "uuid")
    band = get_or_none(Wristband, request.GET["obj_id"])
    if band == None:
        return render(request, "bookings/totem/payment-return.html", {'err': _('Pulsera no encontrada'), 'project': project})

    ppu = ProjectPaytefUser.objects.filter(project_uuid=project.uuid).first()
    if ppu == None or ppu.tcod == "":
        return render(request, "bookings/totem/payment-return.html", {'err': _('Datafono no encontrado'), 'project': project})

    total = band.balance
    try:
        #tcod = ppu.tcod
        tcod = request.session["code"] if "code" in request.session else ""
        payment_ok = manage_transaction(project, -1 * band.balance, "Ticket: {}".format(band.id), tcod)
        if not payment_ok:
            return render(request, "bookings/totem/payment-return.html", {'err': _('Error procesando el pago'), 'project': project})
    except Exception as e:
        print(e)
        return render(request, "bookings/totem/payment-return.html", {'err': _('Error procesando el pago'), 'project': project})

    guest = band.guest

    try:
        send_caldea_payment(project, band, guest)
    except Exception as e:
        print(e)
        return render(request, "bookings/totem/payment-return.html", {'err': _('Error enviando el pago'), 'project': project})

    desc = f'Totem (code: {tcod}): liquidación de importe pendiente'
    band.reset_balance(desc)
    obj = band.make_close()
    if guest.regime != None and guest.regime.code != "DAYP":
        Wristband.reset_band(band)
    return render(request, "bookings/totem/payment-return.html", {'err': '', 'project': project, 'band': band.code, 'total': total})

def totem_view_ticket(request):
    import re
    try:
        band = get_or_none(WristbandBalance, get_param(request.GET, "obj_id"))
        match = re.search(r"data-obj_id='(\d+)'", band.desc)
        fi_id = match.group(1) if match else None

        fi = FormInstance.objects.get(pk = fi_id)
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk)
        context = {'fi': fi, 'index': "0", 'project_uuid': fi.form.project.uuid, 'items':items}
        return render(request, 'bookings/totem/view-ticket.html', context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

def send_caldea_payment(project, band, guest):
    pcu = ProjectCaldeaUser.objects.filter(project_uuid=project.uuid).first()
    if pcu != None and pcu.client_id != "":
        ticket_ids = []
        for item in band.balances.all():
            desc = item.desc.split("#-")
            if len(desc) > 1:
                ticket_ids.append(desc[1][:10])
        reg = guest.regime.code if guest.regime != None else ""
        caldea_send_payment(pcu, band.code, reg, ticket_ids, band.balance)

def totem_print_pay(request):
    try:
        project = get_or_none(Project, get_param(request.GET, "project_uuid"), "uuid")
        band = get_param(request.GET, "band")
        total = get_param(request.GET, "total")
        now = datetime.datetime.now()
        return render(request, 'bookings/totem/print-pay.html', {'project': project, 'band': band, 'total': total, 'date': now})
    except Exception as e:
        print(e)
        logger.error("[bookings-print-ticket] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


