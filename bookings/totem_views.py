from django.contrib import auth
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, reverse_cardkey
from web.models import Project
from bookings.models import Form
from guest.models import Guest
from guest.wristband_models import Wristband, WristbandBalance, WristbandBackup, WristbandBackupBalance
from guest.wristband_lib import close_band_by_regime_and_soft_remove
from connector.models import ProjectPaytefUser
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

def totem_access(request, project_uuid, mobile=""):
    project = get_or_none(Project, project_uuid, "uuid")

    context = {'project_uuid': project.uuid}
    if check_user(request.user):
        next_url = reverse("totem-index", kwargs = context)
    else:
        auth.logout(request)
        next_url = reverse("totem-start")

    form = Form.objects.filter(form_type__code="totem", form_type__project_uuid=project.uuid).first()
    context["next_url"] = next_url
    context["form"] = form
    context["cat"] = form.get_category
    context["mobile"] = mobile
    if mobile != "":
        request.session["mobile"] = mobile
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
            band_err = _("Pulsera no encontrada!")
        elif band.guest == None:
            band_err = _("Pulsera no asignada!")
        elif band.is_close:
            band_err = _("Esta pulsera ya ha sido cerrada!")
        else:
            gr = band.guest.regimes.first()
            regime = gr.regime if gr != None else None

        form = Form.get_totem(project.uuid)
        return render(request, "bookings/totem/view-band.html", {'band':band, 'band_err': band_err, 'form': form, 'project': project})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

#def remove_wristband_backup_balance(wbb):
#    for item in wbb.balances.all():
#        item.delete()
#
#def create_wristband_backup_balance(wb, wbb):
#    for item in wb.balances.all():
#        WristbandBackupBalance.objects.create(date=item.date, amount=item.amount, desc=item.desc, wristband=wbb)
#
#def get_or_update_wristband_backup(wb):
#    wbb = WristbandBackup.objects.filter(code=wb.code, guest_uuid=wb.guest.UUID).first()
#    if wbb == None:
#        wbb = WristbandBackup.objects.create(code=wb.code, guest_uuid=wb.guest.UUID)
#    else:
#        remove_wristband_backup_balance(wbb)
#    wbb.kid = wb.kid
#    wbb.locks = wb.locks
#    wbb.name = wb.name
#    wbb.project_uuid = wb.guest.project_id
#    #wbb.guest_uuid = wb.guest.UUID
#    wbb.guest_name = "{} {}".format(wb.guest.name, wb.guest.surname)
#    wbb.guest_mobile = wb.guest.mobile
#    wbb.guest_email = wb.guest.email
#    wbb.guest_room = wb.guest.room
#    wbb.check_in = wb.guest.check_in
#    wbb.check_out = wb.guest.check_out
#    if wb.type != None:
#        wbb.type = wb.type.name
#    wbb.save()
#    create_wristband_backup_balance(wb, wbb)
#    return wbb

def totem_pay(request):
    project = get_or_none(Project, request.GET["project"], "uuid")
    band = get_or_none(Wristband, request.GET["obj_id"])
    if band == None:
        return render(request, "bookings/totem/payment-return.html", {'err': _('Pulsera no encontrada'), 'project': project})

    ppu = ProjectPaytefUser.objects.filter(project_uuid=project.uuid).first()
    if ppu == None or ppu.tcod == "":
        return render(request, "bookings/totem/payment-return.html", {'err': _('Datafono no encontrado'), 'project': project})

    try:
        tcod = ppu.tcod
        payment_ok = manage_transaction(project, band.balance, "Ticket: {}".format(band.id), tcod)
        if not payment_ok:
            return render(request, "bookings/totem/payment-return.html", {'err': _('Error procesando el pago'), 'project': project})
    except Exception as e:
        print(e)
        return render(request, "bookings/totem/payment-return.html", {'err': _('Error procesando el pago'), 'project': project})

    guest = band.guest
    obj = band.make_close()
    if guest.regime != None and guest.regime.code != "DAYP":
        Wristband.reset_band(band)
    return render(request, "bookings/totem/payment-return.html", {'err': '', 'project': project})

 
