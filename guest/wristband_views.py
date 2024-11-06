from django.conf import settings
from django.http import HttpResponse
from django.contrib import auth
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from .models import Guest, Wristband, WristbandBalance, WristbandType, WristbandLog
from .models import WristbandAccess, WristbandAccessPoint, WristbandAccessZone, WristbandAccessZoneGuest
from web.models import Project, Waiter
from padword.commons import show_exc, get_or_none, get_param, reverse_cardkey, get_float, get_int
from padword.decorators import group_required
from bookings.models import Form
from bookings.common_lib import user_in_group
from connector.models import ProjectStripeUser
from connector.libstripe import ShStripe
from padword.email_lib import send_email

from datetime import datetime

import logging
logger = logging.getLogger(__name__)


'''
    Bands in guest
'''
@group_required("admins", "projects")
def guest_band_details(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        print(guest)
        return render(request, "guest/bands/guest-details-bands.html", {"obj": guest})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_add(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": guest, "step": 0})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_save(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        code = reverse_cardkey(get_param(request.GET, "value"))

        b = Wristband.objects.filter(code=code).first()
        #for b in b_list:
        #    if b != None and b.guest.have_valid_booking():
        if b != None:
            #msg = "There are another user ({} {} - {}) with this band!".format(b.guest.name, b.guest.surname, b.guest.room)
            err = "True"
            return render(request, "guest/bands/guest-details-bands-form.html", {"obj": guest, "band": b, "step": 0, "err": err})
        
        type_list = WristbandType.objects.all()
        band = Wristband.objects.create(guest=guest, code=code)
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": guest, "band": band, "type_list": type_list, "step": 1})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_name(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        band = get_or_none(Wristband, get_param(request.GET, "band_id"))
        band.name = get_param(request.GET, "value")
        band.save()
        type_list = WristbandType.objects.all()
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": guest, "band": band, "type_list": type_list, "step": 2})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_type(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        band = get_or_none(Wristband, get_param(request.GET, "band_id"))
        band.type = get_or_none(WristbandType, get_param(request.GET, "value"))
        band.save()
        type_list = WristbandType.objects.all()
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": guest, "band": band, "type_list": type_list, "step": 3})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_locks(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        if "locks" in request.GET and request.GET["locks"] == "true":
            band.guest.add_all_key_card(band.code, band.name)
            band.locks = True
            band.save()
        type_list = WristbandType.objects.all()
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": band.guest, "band": band, "type_list": type_list, "step": 4})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_kid(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        band.kid = True if "kid" in request.GET and request.GET["kid"] == "true" else False
        band.save()
        type_list = WristbandType.objects.all()
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": band.guest, "band": band, "type_list": type_list, "step": 5})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_balance_add(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        amount = get_float(get_param(request.GET, "balance"))
        if amount > 0:
            balance = WristbandBalance.objects.create(wristband=band, amount=amount, desc=_("Init charge"))
        return render(request, "guest/guest-details-tabs.html", {'obj': band.guest, 'current_tab': 'bands', 'temp_range': range(16,26)})
        #return render(request, "guest/bands/guest-details-bands-list.html", {"obj": band.guest})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_edit(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        type_list = WristbandType.objects.all()
        return render(request, "guest/bands/guest-details-bands-edit-form.html", {"obj": band, "type_list": type_list})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_remove(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        guest = band.guest 
        code = band.code
        band.delete()
        if request.GET["band_lock"] == "true":
            guest.remove_all_key_cards(code)
        return render(request, "guest/bands/guest-details-bands-list.html", {"obj": guest})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_remove2(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "guest"))
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        band_guest = band.guest 
        code = band.code
        band.delete()
        if request.GET["band_lock"] == "true":
            band_guest.remove_all_key_cards(code)
        return render(request, "guest/bands/guest-details-bands-form.html", {"obj": guest, "step": 0})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


@group_required("admins", "projects")
def guest_bands_balance(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        return render(request, "guest/bands/bands.html", {"obj": guest})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_balance_list(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        return render(request, "guest/bands/balance.html", {"band": band})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_balance_form(request):
    try:
        band = get_or_none(Wristband, get_param(request.GET, "obj_id"))
        balance = get_or_none(WristbandBalance, get_param(request.GET, "balance_id"))
        if balance == None:
            balance = WristbandBalance.objects.create(wristband=band)
        return render(request, "guest/bands/balance-form.html", {"obj": balance})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def guest_band_balance_remove(request):
    try:
        balance = get_or_none(WristbandBalance, get_param(request.GET, "obj_id"))
        band = balance.wristband
        balance.delete()
        return render(request, "guest/bands/balance.html", {"band": band})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


@group_required("admins", "projects")
def guest_band_manage_zone(request):
    try:
        guest = get_or_none(Guest, get_param(request.GET, "obj_id"))
        zone = get_or_none(WristbandAccessZone, get_param(request.GET, "zone"))
        band = get_or_none(Wristband, get_param(request.GET, "band"))
        add = get_param(request.GET, "add")
        if add == "True":
            WristbandAccessZoneGuest.objects.get_or_create(guest=guest, zone=zone)
        else:
            obj = WristbandAccessZoneGuest.objects.filter(guest=guest, zone=zone).first()
            if obj != None:
                obj.delete()
        return render(request, "guest/bands/access-points.html", {"obj": guest, "band": band})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


'''
    Wristbands
'''
@group_required("admins")
def wristbands(request):
    return render (request, "wristbands/wristbands.html", {'active': 'searchbands'})

@group_required("admins")
def wristbands_search(request):
    value = reverse_cardkey(get_param(request.GET, "value"))
    band_result = Wristband.objects.filter(code=value)
    return render (request, "wristbands/wristbands-search.html", {'band_list': band_result, 'band_code': value})

'''
    Wristbands by project
'''
@group_required("projects")
def wristbands_by_project(request):
    try:
        return render (request, "wristbands-by-project/wristbands.html", {'active': 'searchbands'})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def wristbands_search_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        value = reverse_cardkey(get_param(request.GET, "value"))
        band_result = Wristband.objects.filter(code=value, guest__project_id=project.uuid)
        return render (request, "wristbands-by-project/wristbands-search.html", {'band_list': band_result, 'band_code': value})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

'''
    Wristbands Access
'''
@group_required("admins")
def wristbands_access(request):
    return render (request, "wristbands/access/wristbands.html", {'active': 'wristbands-access'})

@group_required("admins")
def wristbands_access_search(request):
    value = reverse_cardkey(get_param(request.GET, "value"))
    band_result = Wristband.objects.filter(code=value).first()
    return render (request, "wristbands/access/wristbands-search.html", {'band': band_result, 'band_code': value})

def wristbands_access_index(request, project_uuid, point_uuid):
    try:
        project = get_or_none(Project, project_uuid, "uuid")
        ap = get_or_none(WristbandAccessPoint, point_uuid, "uuid")

        return render(request, "wristbands/access/index.html", {'project': project, 'access_point': ap})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

def wristbands_access_check(last_access, ap, band):
    if last_access == None:
        #Primer acceso
        if not ap.in_point:
            msg = _("Error!, Este es un punto de salida y no se ha registrado ninguna entrada")
            return True, msg
        else:
            msg = _('Ha entrado correctamente!')
            WristbandAccess.objects.create(wristband=band, inside=True)
            return False, msg
    else:
        #Esta fuera
        if not last_access.inside:
            #Punto de salida
            if not ap.in_point:
                msg = _("Error!, Este es un punto de salida y no se ha registrado ninguna entrada")
                return True, msg
            #Punto de entrada
            else:
                msg = _('Ha entrado correctamente!')
                WristbandAccess.objects.create(wristband=band, inside=True)
                return False, msg
        #Esta dentro
        else:
            #Punto de salida
            if not ap.in_point:
                msg = _('Ha salido correctamente!')
                WristbandAccess.objects.create(wristband=band, inside=False)
                return False, msg
            #Punto de entrada
            else:
                msg = _("Error!, Este es un punto de entrada y no se ha registrado ninguna salida")
                return True, msg

def wristbands_access_send(request):
    try:
        project_uuid = get_param(request.GET, "obj_id")
        point_uuid = get_param(request.GET, "point")
        project = get_or_none(Project, project_uuid, "uuid")
        ap = get_or_none(WristbandAccessPoint, point_uuid, "uuid")
        code = get_param(request.GET, "value")

        if "lg" in request.GET:
            code = reverse_cardkey(code)
            
        if ap == None:
            msg = _("Error!, No se encuentra el punto de acceso")
            return render(request, "wristbands/access/result.html", {'error':True, 'msg': msg})

        band = Wristband.get_active_by_project(project, code)
        if band == None:
            msg = _("Error!, Por favor revise que:<br/>- La pulsera está dada de alta<br/>- Las fechas de uso son correctas")
            return render(request, "wristbands/access/result.html", {'error':True, 'msg': msg})
            
        last_access = band.access.all().order_by("-id").first()
        err, msg = wristbands_access_check(last_access, ap, band)
        return render(request, "wristbands/access/result.html", {'error': err, 'msg': msg})
    except Exception as e:
        print(e)
        return render(request, "wristbands/pay-result.html", {'error':True, 'msg': e})
        #return render(request, "error_exception.html", {'exc':show_exc(e)})


'''
    Wristbands Direct Pay
'''
def check_user(user):
    if not user.is_authenticated:
        return False
    if not user_in_group(user, "waiters"):
        return False
    return True

def pay_access(request, project_uuid):
    project = get_or_none(Project, project_uuid, "uuid")

    context = {'project_uuid': project.uuid}
    if check_user(request.user):
        next_url = reverse("wristband-pay-index", kwargs = context)
    else:
        auth.logout(request)
        next_url = reverse("wristband-pay-login-form")

    form = Form.objects.filter(form_type__code="wb-pay", form_type__project_uuid=project.uuid).first()
    context["next_url"] = next_url
    context["cat"] = form.get_category
    return render(request, 'wristbands/pay-welcome.html', context)

def pay_login_form(request):
    return render(request, "wristbands/pay-form-login.html", {'project_uuid': request.GET["project_uuid"], 'error': ''})

def pay_login(request):
    '''
        Guest access by form
    '''
    try:
        project_uuid = request.POST["project_uuid"]
        username = request.POST["username"]
        password = request.POST["password"]

        if username == "" or password == "":
            err = _('You must to complete username and password!')
            return render(request, "wristbands/pay-form-login.html", {'project_uuid': project_uuid, 'error': err})

        project = get_or_none(Project, project_uuid, "uuid")

        user = auth.authenticate(request, username=username, password=password)
        if user is None:
            err = _('Username or password incorrect!')
            return render(request, "wristbands/pay-form-login.html", {'project_uuid': project_uuid, 'error': err})

        waiter = Waiter.objects.filter(username = username, project_uuid = project.uuid).first()
        if waiter == None:
            err = _('Waiter not found!')
            return render(request, "wristbands/pay-form-login.html", {'project_uuid': project_uuid, 'error': err})

        auth.login(request, user)

        return redirect(reverse("wristband-pay-index", kwargs = {'project_uuid': project_uuid}))
    except Exception as e:
        logger.error("[pay-login] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("waiters")
def pay_index(request, project_uuid):
    try:
        project = get_or_none(Project, project_uuid, "uuid")

        return render(request, "wristbands/pay-index.html", {'project': project})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def pay_send(request):
    try:
        project_uuid = get_param(request.GET, "obj_id")
        project = get_or_none(Project, project_uuid, "uuid")
        code = get_param(request.GET, "value")
        amount = get_float(get_param(request.GET, "amount"))
        amount = get_int(round(amount, 2) * 100)

        if "lg" in request.GET:
            code = reverse_cardkey(code)
            
        if amount == 0:
            return render(request, "wristbands/pay-result.html", {'error':True, 'msg': _('Error: No ha introducido un importe!')})
            #return HttpResponse(_('Error: No ha introducido un importe!'))

        band = Wristband.get_active_by_project(project, code)
        if band == None:
            msg = _("Error!, Por favor revise que:<br/>- La pulsera está dada de alta<br/>- Las fechas de uso son correctas")
            return render(request, "wristbands/pay-result.html", {'error':True, 'msg': msg})
            #return render(request, "wristbands/pay-result.html", {'error':True, 'msg': _('Error: Pulsera no encontrada!')})
            
        #guest = band.guest
        #if not guest.have_valid_booking():
        #    return render(request, "wristbands/pay-result.html", {'error':True, 'msg': _('Error: El huésped no tiene una reserva válida!')})

        #if guest.project_id != project_uuid:
        #    return render(request, "wristbands/pay-result.html", {'error':True, 'msg': _('Error: La pulsera no es válida!')})

        guest = band.guest
        psu = ProjectStripeUser.objects.filter(project_uuid=guest.project_id).first()
        if psu is None:
            return render(request, "wristbands/pay-result.html", {'error':True, 'msg': _('No se ha encontrado la Api Key!')})
            #return HttpResponse(_('No se ha encontrado la Api Key!'))

        guest_name = "{} {}".format(guest.name, guest.surname)
        gs = guest.stripe
        gc = guest.card

        st = ShStripe(psu.api_key)
        obj_id, next_action = st.create_stripe_payment_intent(gs.stripe_id, gs.payment_method, amount, "eur")
        if obj_id == "" or obj_id == None:
            return render(request, "wristbands/pay-result.html", {'error':True, 'msg': _('Error procesando el pago!')})
            #return HttpResponse(_('Error procesando el pago!'))

        add_log_to_band(guest_name, amount, band)

        try:
            pay_send_email(amount, guest.email)
        except Exception as e:
            print(e)

        #msg = _('El pago se ha añadido correctamente al huésped: {}!'.format(guest_name))
        #return render(request, "wristbands/pay-result.html", {'error':False, 'msg': msg, 'next_action': next_action})
        form = Form.objects.filter(form_type__code="wb-pay", form_type__project_uuid=project.uuid).first()
        return render(request, "wristbands/pay-result-success.html", {'desc': form.desc, 'date': datetime.now(), 'guest': guest_name, 'band': band.name, 'amount': amount, 'next_action': next_action})
    except Exception as e:
        print(e)
        return render(request, "wristbands/pay-result.html", {'error':True, 'msg': e})
        #return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def pay_close(request):
    auth.logout(request)
    project_uuid = request.GET["project_uuid"] if "project_uuid" in request.GET else ""
    return redirect(reverse("wristband-pay-access", kwargs = {'project_uuid': project_uuid}))

@group_required("waiters")
def pay_confirm(request):
    #project_uuid = request.GET["project_uuid"] if "project_uuid" in request.GET else ""
    return render(request, "wristbands/pay-confirm.html", {})

def add_log_to_band(guest_name, amount, band):
    try:
        str_amount = "{:.2f}".format(float(amount)/100)
    except:
        str_amount = "---"
    desc = _("Pago directo con tarjeta del huésped {} por un importe de {} euros".format(guest_name, str_amount))
    WristbandLog.objects.create(desc=desc, wristband=band)

def pay_send_email(amount, email):
    subject = "Pago con tarjeta {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    body = "Ha realizado un pago con tarjeta por un importe de {} euros".format(amount) 
    send_email(subject, body, settings.EMAIL_FROM_DEFAULT, [email])



