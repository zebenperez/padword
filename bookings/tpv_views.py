from django.contrib import auth
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, reverse_cardkey
from web.models import Project, Waiter, Room
from contents.models import Category, ShoppingCart, Item, PaymentType, PointOfSale, Table, PosCodeItem
from guest.models import Guest
from guest.wristband_models import Wristband, WristbandBalance
#from web.lock_lib import ShLock
from connector.winhotel_lib import send_charge, write_log as wh_write_log
from connector.models import ProjectWinhotelUser

from .common_lib import get_or_create_form_instance_tpv, get_or_create_form_instance_info_tpv
from .common_lib import user_in_group, get_or_create_form_instance_info_client_tpv
from .tpv_lib import get_cash_zeta, update_cash, get_number_x
from .tpv_winhotel_lib import get_food_total, get_drinks_total, get_breakfast_total, cash_daily_summary
from .tpv_winhotel_lib import cash_send_daily_summary, cash_send_charges, get_source_total 
from .tpv_paytef_lib import manage_transaction
from .models import Form, FormInstance, Status, Cash
from django.conf import settings

import datetime
import json
import logging
import time
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

def tpv_access(request, project_uuid, mobile=""):
    project = get_or_none(Project, project_uuid, "uuid")

    context = {'project_uuid': project.uuid}
    if check_user(request.user):
        next_url = reverse("tpv-index", kwargs = context)
    else:
        auth.logout(request)
        next_url = reverse("tpv-login-form")

    form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=project.uuid).first()
    context["next_url"] = next_url
    context["cat"] = form.get_category
    context["mobile"] = mobile
    return render(request, 'bookings/tpv/tpv-welcome.html', context)

def tpv_login_form(request):
    mobile = get_param(request.GET, "mobile")
    if mobile != "":
        request.session["mobile"] = mobile
    return render(request, "bookings/tpv/tpv-form-login.html", {'project_uuid': request.GET["project_uuid"], 'error': ''})

def tpv_login(request):
    '''
        Guest access by form
    '''
    try:
        project_uuid = request.POST["project_uuid"]
        username = request.POST["username"]
        password = request.POST["password"]

        if username == "" or password == "":
            err = _('You must to complete username and password!')
            return render(request, "bookings/tpv/tpv-form-login.html", {'project_uuid': project_uuid, 'error': err})

        project = get_or_none(Project, project_uuid, "uuid")

        user = auth.authenticate(request, username=username, password=password)
        if user is None:
            err = _('Username or password incorrect!')
            return render(request, "bookings/tpv/tpv-form-login.html", {'project_uuid': project_uuid, 'error': err})

        waiter = Waiter.objects.filter(username = username, project_uuid = project.uuid).first()
        if waiter == None:
            err = _('Waiter not found!')
            return render(request, "bookings/tpv/tpv-form-login.html", {'project_uuid': project_uuid, 'error': err})

        auth.login(request, user)

        return redirect(reverse("tpv-index", kwargs = {'project_uuid': project_uuid}))
    except Exception as e:
        logger.error("[tpv-login] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("waiters")
def tpv_index(request, project_uuid):
    try:
        project = get_or_none(Project, project_uuid, "uuid")

        if "point_of_sale" not in request.session or request.session["point_of_sale"] == "":
            project = get_or_none(Project, project_uuid, "uuid")
            point_of_sales = PointOfSale.objects.filter(project_uuid=project.uuid).order_by("order")
            return render(request, "bookings/tpv/index.html", {'point_of_sales': point_of_sales, 'project_uuid':project.uuid})
        elif "table" not in request.session or request.session["table"] == "":
            pos = get_or_none(PointOfSale, request.session["point_of_sale"])
            #date = datetime.datetime.strptime("{} 23:59:59".format(datetime.datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d %H:%M:%S")
            #cash, created = get_cash(pos, date, request.user.username)
            cash, created = get_cash_zeta(pos, request.user.username)
            tables = Table.objects.filter(point_of_sale=pos)
            context = {'pos': pos, 'tables': tables, 'cash': cash, 'created': created, 'project_uuid': project.uuid}
            return render(request, "bookings/tpv/index.html", context)
        else:
            form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=project.uuid).first()
            pos = get_or_none(PointOfSale, request.session["point_of_sale"])
            table = get_or_none(Table, request.session["table"])
            fi = get_or_create_form_instance_tpv(form, pos.uuid, table.uuid, request.user.username)
            fi_info = get_or_create_form_instance_info_tpv(fi, pos.name, table.name)
            cat_list = [item.category for item in pos.categories.all()]
            item_favorites = []
            for cat in cat_list:
                item_favorites += list(cat.get_items_favorites)
            item_commons = form.get_common_items()

            #band = Wristband.get_active_by_project(fi.form.project, fi_info.band)

            #template = request.GET["template"] if "template" in request.GET and request.GET["template"] != "" else "index"
            context = {
                'project_uuid':project.uuid, 
                'form':form, 
                'fi': fi, 
                'pos': pos, 
                'table': table, 
                #'band': band, 
                'cat_list': cat_list,
                #'table_list': Table.objects.filter(project_uuid=project.uuid),
                'item_favorites': item_favorites,
                'item_commons': item_commons
            }

            return render(request, "bookings/tpv/index.html", context)
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_set_pos(request):
    try:
        pos = get_or_none(PointOfSale, request.GET["obj_id"])
        request.session["point_of_sale"] = pos.id
        return redirect(reverse("tpv-index", kwargs = {'project_uuid': pos.project_uuid}))
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_change_pos(request):
    try:
        request.session["point_of_sale"] = ""
        request.session["table"] = ""
        return redirect(reverse("tpv-index", kwargs = {'project_uuid': request.GET["project_uuid"]}))
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_set_table(request):
    try:
        table = get_or_none(Table, request.GET["obj_id"])
        request.session["table"] = table.id
        return redirect(reverse(request.GET["index"], kwargs = {'project_uuid': table.point_of_sale.project_uuid}))
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_change_table(request):
    try:
        request.session["table"] = ""
        return redirect(reverse("tpv-index", kwargs = {'project_uuid': request.GET["project_uuid"]}))
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_set_cash(request):
    try:
        cash = get_or_none(Cash, request.GET["obj_id"])
        cash.ini_cash = request.GET["value"]
        cash.save()
        return redirect(reverse(request.GET["index"], kwargs = {'project_uuid': cash.project_uuid}))
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_ticket(request):
    try:
        fi = get_or_none(FormInstance, request.GET["obj_id"])
        val = get_param(request.GET, "value", "")
        if val != "":
            band = Wristband.objects.filter(code = reverse_cardkey(val), guest__deleted=False)
            #print("--1--")
            #print(val)
            #for b in band:
            #    print("{} {}".format(b.guest.name, b.guest.surname))
        return render(request, "bookings/tpv/view-ticket.html", {'fi':fi,})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_check_band(request):
    try:
        fi = get_or_none(FormInstance, request.GET["obj_id"])
        val = get_param(request.GET, "value", "")
        #band = Wristband.objects.filter(code = reverse_cardkey(val), guest__project_id=fi.form.project.uuid, guest__deleted=False).first()
        band = Wristband.get_active_by_project(fi.form.project, reverse_cardkey(val))
        regime = None
        band_err = ""
        if band != None and band.guest != None:
            #if band.type != None and band.type.code == "00":
            #    band = None
            #    band_err = _("This band is locked!")
            #else:
            gr = band.guest.regimes.first()
            regime = gr.regime if gr != None else None
            get_or_create_form_instance_info_client_tpv(fi, band.guest, band.code, band.name)
            #fi.update_items_low_price()
            fi.update_items_prices()
        else:
            band_err = _("This band is not asigned to any guest!")

        return render(request, "bookings/tpv/view-ticket.html", {'fi':fi, 'band_err': band_err})
        #band_err = True if band == None else False
        #return render(request, "bookings/tpv/view-ticket.html", {'fi':fi, 'band': band, 'regime': regime, 'band_err': band_err})
        #return render(request, "bookings/tpv/view-guest-info.html", {'fi':fi, 'band': band, 'regime': regime})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_check_room(request):
    try:
        fi = get_or_none(FormInstance, request.GET["obj_id"])
        val = get_param(request.GET, "value", "")

        project = fi.form.project
        room = Room.objects.filter(project_uuid=project.uuid, number=val).first()
        if room == None:
            return render(request, "bookings/tpv/view-ticket.html", {'fi':fi, 'band_err':_("Room not found!")})
        guest = room.current_guest
        if guest == None:
            return render(request, "bookings/tpv/view-ticket.html", {'fi':fi, 'band_err':_("Guest not found!")})

        get_or_create_form_instance_info_client_tpv(fi, guest, "", "")
        fi.update_items_prices_guest(guest)
        return render(request, "bookings/tpv/view-ticket.html", {'fi':fi, 'band_err': "", "guest": guest})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_add_item(request):
    try:
        form_id = request.GET["form_id"]
        item_id = request.GET["item_id"]
        fi = get_or_none(FormInstance, int(form_id))
        item = get_or_none(Item, int(item_id))

        #obj = ShoppingCart.objects.create(form_instance_id=fi.id,item=item,category=item.category.name,name=item.name,price=item.price,comments='')
        #fi.update_item_low_price(obj)
        #fi.update_item_discount_price(obj)

        obj = ShoppingCart.objects.create(form_instance_id=fi.id,item=item,category=item.category.name,name=item.name,comments='')
        fi.update_item_prices(obj)

        instance = FormInstance.objects.get(pk=form_id)
        return render(request, "bookings/tpv/view-ticket.html", {'fi':instance,})

        #mobile = get_param(request.GET, "mobile")
        #temp = "view-ticket-mobile.html" if mobile != "" else "view-ticket.html"

        #instance = FormInstance.objects.get(pk=form_id)
        #return render(request, "bookings/tpv/{}".format(temp), {'fi':instance,})
        #items = instance.items_in_bookings(item).count()
        #return render(request, "bookings/tpv/show-instance-result.html", {'fi':instance,'item':item,'items':items})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_order_remove(request):
    try:
        #fi_id = request.GET["obj_id"]
        #fi = get_or_none(FormInstance, fi_id)
        #form = fi.form
        #fi.delete()
        fi = get_or_none(FormInstance, request.GET["obj_id"])
        fi.set_status("05", request.user, "")
        request.session["table"] = ""

        #return redirect(reverse("tpv-index", kwargs = {'project_uuid': form.project.uuid}))
        mobile = get_param(request.GET, "mobile")
        if mobile != "":
            return redirect(reverse("tpv-mob-index", kwargs = {'project_uuid': fi.form.project.uuid}))
        else:
            return redirect(reverse("tpv-index", kwargs = {'project_uuid': fi.form.project.uuid}))
    except Exception as e:
        print(e)
        logger.error("[bookings-remove_fi] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("waiters")
def tpv_order_item_remove(request):
    try:
        item_id = request.GET["item_id"]
        obj = get_or_none(ShoppingCart, item_id)
        fi = get_or_none(FormInstance, obj.form_instance_id)
        obj.delete()

        return render(request, "bookings/tpv/view-ticket.html", {'fi':fi,})

        #mobile = get_param(request.GET, "mobile")
        #temp = "view-ticket-mobile.html" if mobile != "" else "view-ticket.html"

        #return render(request, "bookings/tpv/{}".format(temp), {'fi':fi,})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_order_item_comment(request):
    try:
        item_id = get_param(request.GET, "item_id")
        form_id = get_param(request.GET, "form_id")
        mobile = get_param(request.GET, "mobile")
        obj = get_or_none(ShoppingCart, int(item_id))
        return render(request, "bookings/tpv/shopping-form.html", {'obj':obj, 'form_id':form_id, 'mobile': mobile})
        #temp = get_param(request.GET, "template")
        #template = "bookings/tpv/{}.html".format(temp) if temp != "" else "bookings/tpv/shopping-form.html"
        #mobile = get_param(request.GET, "mobile")
        #temp = "shopping-form-mobile.html" if mobile != "" else "shopping-form.html"

        #return render(request, "bookings/tpv/{}".format(temp), {'obj':obj, 'form_id':form_id})
        #return render(request, template, {'obj':obj, 'form_id':form_id})
        #return render(request, "bookings/tpv/shopping-form.html", {'obj':obj, 'form_id':form_id})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

def add_balance_to_band(pos, fi, band):
    url = "/bookings/booking-guest-view/"
    desc = "Ticket from {}: ".format(pos.name)
    desc += "<a class='ark' data-url='{}' data-target-modal='common-modal' data-obj_id='{}'> #{}</a>".format(url, fi.id, fi.get_index)
    WristbandBalance.objects.create(amount=(get_float(fi.amount)*-1), desc=desc, wristband=band)

def set_desc(fi, desc):
    if desc != "":
        try:
            info = fi.details
        except:
            info = FormInstanceInfo.objects.create(fi = fi)
        info.desc = desc
        info.save()

def tpv_order_send_room(fi, pt, local_date, factor, project, request):
    wh_write_log("ORDER: {} ({})".format(fi.id, local_date.strftime("%Y-%m-%d %H:%M:%S")))
    details = fi.details
    if pt != None and (pt.code == "08" or pt.code == "0408") and details != None and details.client_room != "":
        pos = get_or_none(PointOfSale, request.session["point_of_sale"])
        room = Room.objects.filter(project_uuid=project.uuid, number=details.client_room).first()
        guest = room.current_guest

        #wh_write_log("--> PAGO CON PULSERA: {}".format(band_id))
        if guest != None and (pt.code == "08" or pt.code == "0408"):
            pwu = get_or_none(ProjectWinhotelUser, project.uuid, "project_uuid")
            if pwu != None and pwu.source_code != "":
                wh_write_log("----> SE ENVIA EL CARGO: {} ({})".format(guest.name, details.client_room))
                send_charges_guest(pwu, fi, guest, pos, factor)

@group_required("waiters")
def tpv_order_send(request):
    try:
        fi_id = get_param(request.GET, "obj_id")
        pt_code = get_param(request.GET, "payment_type", "")
        subtotal = get_param(request.GET, "subtotal", "")
        total = get_param(request.GET, "total", "")
        band_id = get_param(request.GET, "band", "")
        desc = get_param(request.GET, "desc", "")
        mobile = get_param(request.GET, "mobile", "")

        fi = get_or_none(FormInstance, fi_id)
        project = fi.form.project

        #Formulario ya enviado
        if fi.current_status("01"):
            context = {'msg': "00", 'fi': fi, 'project_uuid': project.uuid, "mobile": mobile}
            return render(request, 'bookings/tpv/show-msg.html', context)

        pt = get_or_none(PaymentType, pt_code, "code")

        #Pago con paytef
        if pt.code == "06":
            tcod = request.session["mobile"] if "mobile" in request.session else ""
            payment_ok = manage_transaction(project, total, "Ticket: {}".format(fi.get_index), tcod)
            if not payment_ok:
                context = {'msg': "00", 'fi': fi, 'project_uuid': project.uuid, "mobile": mobile}
                return render(request, 'bookings/tpv/show-msg.html', context)

        #Devolución con paytef
        if pt.code == "0406":
            tcod = request.session["mobile"] if "mobile" in request.session else ""
            payment_ok = manage_transaction(project, total, "Ticket: {}".format(fi.get_index), tcod, "refund")
            if not payment_ok:
                context = {'msg': "00", 'fi': fi, 'project_uuid': project.uuid, "mobile": mobile}

        #Cargo en habitación
        guest = None
        partner = ""
        if pt.code == "07":
            room = get_param(request.GET, "room", "")
            partner = get_param(request.GET, "partner", "")
            now = datetime.datetime.now()
            guest = Guest.objects.filter(project_id=partner, room=room, check_in__lte=now, check_out__gte=now).first()
            if guest == None:
                context = {'msg': "07", 'fi': fi, 'project_uuid': project.uuid, "mobile": mobile}
                return render(request, 'bookings/tpv/show-msg.html', context)

        local_date = project.local_date(datetime.datetime.now())
        fi.set_status("01", request.user, "")
        #fi.date = datetime.datetime.now()
        fi.date = local_date
        fi.amount = total

        factor = 1
        if "04" in pt.code:
            factor = -1
            fi.update_items_prices_return()

        #fi.amount = amount if amount_user == "" else amount_user
        #factor = -1 if get_float(amount.replace(",", ".")) < 0 else 1
        #if pt_code != "":
        fi.payment_type = pt
        fi.save()
        fi.update_index()
        fi.send_items()

        wh_write_log("ORDER: {} ({})".format(fi.id, local_date.strftime("%Y-%m-%d %H:%M:%S")))
        if pt != None and (pt.code == "03" or pt.code == "0403") and band_id != "":
            pos = get_or_none(PointOfSale, request.session["point_of_sale"])
            band = get_or_none(Wristband, band_id)
            add_balance_to_band(pos, fi, band)

            #wh_write_log("--> PAGO CON PULSERA: {}".format(band_id))
            if band != None and (pt.code == "03" or pt.code == "0403"):
                pwu = get_or_none(ProjectWinhotelUser, project.uuid, "project_uuid")
                if pwu != None and pwu.source_code != "":
                    wh_write_log("----> SE ENVIA EL CARGO: {} ({})".format(band.name, band.code))
                    #send_charges(pwu, fi, band, pos, factor)
                    send_charges2(pwu, fi, band, pos, factor)

        #Cargo en habitación local
        tpv_order_send_room(fi, pt, local_date, factor, project, request)

        #Cargo en habitación
        if pt.code == "07" and guest != None and partner != "":
            pos = get_or_none(PointOfSale, request.session["point_of_sale"])
            pwu = get_or_none(ProjectWinhotelUser, partner, "project_uuid")
            wh_write_log("----> SE ENVIA EL CARGO EN HABITACIÓN: {} ({})".format(guest.name, guest.room))
            #send_charges(pwu, fi, guest, pos, factor)
            send_charges_room(pwu, fi, guest, pos, factor)

        set_desc(fi, desc)

        context = {'msg': fi.get_status.status.code, 'project_uuid': project.uuid, "mobile": mobile, 'fi': fi}
        #context = {'msg': fi.get_status.status.code, 'project_uuid': fi.form.project.uuid}
        return render(request, 'bookings/tpv/show-msg.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-booking_send] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("waiters")
def tpv_order_send_part(request):
    try:
        fi_id = get_param(request.GET, "obj_id")
        mobile = get_param(request.GET, "mobile", "")

        fi = get_or_none(FormInstance, fi_id)
        fi.send_items()

        fi.date = fi.project.local_date(datetime.datetime.now())
        fi.save()

        mobile = get_param(request.GET, "mobile")
        if mobile != "":
            return render(request, "bookings/tpv/mobile/view-ticket.html", {'fi':fi,})
        else:
            return render(request, "bookings/tpv/view-ticket.html", {'fi':fi,})
    except Exception as e:
        print(e)
        logger.error("[bookings-booking_send] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("waiters")
def tpv_print_ticket(request, obj_id):
    try:
        #fi = get_or_none(FormInstance, get_param(request.GET, "obj_id"))
        fi = get_or_none(FormInstance, obj_id)
        mobile = get_param(request.GET, "mobile", "")
        return render(request, 'bookings/tpv/print-ticket.html', {'fi': fi, 'info': fi.details, 'mobile': mobile})
    except Exception as e:
        print(e)
        logger.error("[bookings-print-ticket] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("waiters")
def tpv_print_ticket2(request):
    try:
        fi = get_or_none(FormInstance, get_param(request.GET, "obj_id"))
        #fi = get_or_none(FormInstance, obj_id)
        mobile = get_param(request.GET, "mobile", "")
        return render(request, 'bookings/tpv/print-ticket.html', {'fi': fi, 'info': fi.details, 'mobile': mobile})
    except Exception as e:
        print(e)
        logger.error("[bookings-print-ticket] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


@group_required("waiters")
def orders_by_waiter(request, project_uuid=None):
    msg = ""
    try:
        if project_uuid == None:
            project_uuid = request.GET["project_uuid"]

        waiter = Waiter.objects.filter(username = request.user.username, project_uuid = project_uuid).first()
        if waiter == None:
            return render(request, 'error_exception.html', {'exc': 'User not found!'})

        cat_uuid = request.GET["cat_id"] if "cat_id" in request.GET else ""
        context = {
            'items': FormInstance.objects.filter(guest_name=request.user.username, status_list__isnull=False).distinct(),
            'status_list': Status.objects.all(),
            'cat_uuid': cat_uuid,
            'waiter': waiter
        }
        return render (request, "bookings/tpv/orders-by-waiter.html", context)
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
        msg = str(e)
        return render(request, 'error_exception.html', {'exc': str(e)})

@group_required("waiters")
def order_details(request):
    try:
        fi_id = request.GET["obj_id"]
        fi = FormInstance.objects.get(pk = fi_id)
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk)

        cat_uuid = request.GET["cat_id"] if "cat_id" in request.GET else ""
        context = {'fi': fi, 'index': "0", 'project_uuid': fi.form.project.uuid, 'items':items, 'cat_uuid': cat_uuid}
        return render(request, 'bookings/tpv/order-details.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-fill_form] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("waiters")
def cash_z(request):
    try:
        cash = get_or_none(Cash, request.GET["obj_id"]) 
        update_cash(cash, request.user, True)
        cash.close_date = cash.project.local_date(datetime.datetime.now())
        cash.close = True
        cash.save()
        
        pwu = ProjectWinhotelUser.objects.filter(project_uuid=cash.project_uuid).first()
        if pwu != None:
            cash_daily_summary(cash.pos, cash.date.strftime("%Y-%m-%d"))
            cash_send_daily_summary(cash.project_uuid, cash.pos, cash.date.strftime("%Y-%m-%d"))
            #cash_send_charges(cash)

        return redirect(reverse(request.GET["index"], kwargs = {'project_uuid': cash.project_uuid}))
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("waiters")
def cash_x(request):
    try:
        cash = get_or_none(Cash, request.GET["obj_id"]) 
        cash_x = cash
        cash_x.pk = None
        cash_x.number = get_number_x(cash.pos_uuid)
        cash_x.zeta = False
        cash_x.date = cash.project.local_date(datetime.datetime.now())
        cash_x.save()
        update_cash(cash_x, request.user)
        cash_x.close = True
        cash_x.close_date = cash.project.local_date(datetime.datetime.now())
        cash_x.save()
        return render(request, 'bookings/tpv/tpv-tables-x.html', {'cash': cash, 'back_url': request.GET["back"]})
        #return redirect(reverse(request.GET["index"], kwargs = {'project_uuid': cash.project_uuid}))
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("waiters")
def print_z(request):
    try:
        cash = get_or_none(Cash, request.GET["obj_id"])
        return render(request, "bookings/tpv/print-z.html", {'obj': cash,})
    except Exception as e:
        return HttpResponse("Error: {}".format(e))

@group_required("waiters")
def tpv_close(request):
    auth.logout(request)
    project_uuid = request.GET["project_uuid"] if "project_uuid" in request.GET else ""
    #return redirect(tpv_access, project_uuid)
    return redirect(reverse("tpv-access", kwargs = {'project_uuid': project_uuid}))


'''
    WINHOTEL
'''
#from django.db.models import Sum
#def get_drinks_total(fi, band):
#    #total = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__lt=50000).aggregate(Sum('item__price'))["item__price__sum"]
#    #return total if total != None else -1
#
#    regime = band.guest.regime.code if band != None and band.guest != None and band.guest.regime != None else ""
#    if regime == "":
#        total = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__lt=50000).aggregate(Sum('price'))["price__sum"]
#    else:
#        total = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__lt=50000).aggregate(Sum('low_price'))["low_price__sum"]
#    return total
#    #return total if total != None else -1
#
#    #total = -1
#    #item_list = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__lt=50000)
#    #for item in item_list:
#    #    total += item.item.get_price(regime)
#    #return total

#def get_food_total(fi, band):
#    #total =  ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__gte=50000).aggregate(Sum('item__price'))["item__price__sum"]
#    #return total if total != None else -1
#
#    regime = band.guest.regime.code if band != None and band.guest != None and band.guest.regime != None else ""
#    if regime == "":
#        total = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__gte=50000).aggregate(Sum('price'))["price__sum"]
#    else:
#        total = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__gte=50000).aggregate(Sum('low_price'))["low_price__sum"]
#    return total
#    #return total if total != None else -1
#
#    #total = -1
#    #item_list = ShoppingCart.objects.filter(form_instance_id=fi.pk, item__ext_id__gte=50000)
#    #for item in item_list:
#    #    total += item.item.get_price(regime)
#    #return total

def send_charges(pwu, fi, band, pos, factor):
    #pau = get_or_none(ProjectWinhotelUser, fi.form.project.uuid, "project_uuid")
    booking_code = band.guest.ext_id
    room_code = band.guest.room
    contact_name = "{} {}".format(band.guest.name, band.guest.surname)
    contact_id = band.guest.ext_id
    has_credit = "true"
    limit_credit = 0
    #source
    #source = fi.id
    s_drink = pos.code1
    s_food = pos.code2
    s_break = pos.code3
    #source_document
    sd_drink = "Cargo Ticket Nº-{} / TPV {} (Bebidas)".format(fi.id, pos.name)
    sd_food = "Cargo Ticket Nº-{} / TPV {} (Comidas)".format(fi.id, pos.name)
    sd_break = "Cargo Ticket Nº-{} / TPV {} (Desayunos)".format(fi.id, pos.name)
    date = fi.date.strftime("%Y-%m-%dT%H:%M:%S")
    #total_amount
    #total_amount = fi.get_total()
    #ta_drink = get_drinks_total(fi, band) * factor
    #ta_food = get_food_total(fi, band) * factor
    ta_drink = get_drinks_total(fi, band)
    ta_food = get_food_total(fi, band)
    ta_break = get_breakfast_total(fi, band)
    cash_code = ""
    #print(ta_drink)
    #print(ta_food)

    if ta_drink != None:
        #wh_write_log("------> BEBIDAS")
        send_charge(pwu,booking_code,room_code,contact_name,contact_id,has_credit,limit_credit,s_drink,sd_drink,date,ta_drink*factor,cash_code)
    if ta_food != None:
        #wh_write_log("------> COMIDAS")
        send_charge(pwu,booking_code,room_code,contact_name,contact_id,has_credit,limit_credit,s_food,sd_food,date,ta_food*factor,cash_code)
    if ta_break != None:
        #wh_write_log("------> DESAYUNO")
        send_charge(pwu,booking_code,room_code,contact_name,contact_id,has_credit,limit_credit,s_break,sd_break,date,ta_break*factor,cash_code)

def send_charges2(pwu, fi, band, pos, factor):
    b_code = band.guest.ext_id
    room_code = band.guest.room
    cont_name = "{} {}".format(band.guest.name, band.guest.surname)
    cont_id = band.guest.ext_id
    has_credit = "true"
    limit_credit = 0
    date = fi.date.strftime("%Y-%m-%dT%H:%M:%S")

    source_list = PosCodeItem.get_codes_by_project(fi.project.uuid, pos.ext_code)
    for source in source_list:
        s_desc = "Cargo Ticket Nº-{} / TPV {} ({})".format(fi.id, pos.name, source)
        s_total = get_source_total(fi, source)
        cash_code = ""
        wh_write_log("------> Source: {} - Total: {}".format(source, s_total))
        print("------> Source: {} - Total: {}".format(source, s_total))
        send_charge(pwu,b_code,room_code,cont_name,cont_id,has_credit,limit_credit,source,s_desc,date,s_total*factor,cash_code)

def send_charges_guest(pwu, fi, guest, pos, factor):
    b_code = guest.ext_id
    room_code = guest.room
    cont_name = "{} {}".format(guest.name, guest.surname)
    cont_id = guest.ext_id
    has_credit = "true"
    limit_credit = 0
    date = fi.date.strftime("%Y-%m-%dT%H:%M:%S")

    source_list = PosCodeItem.get_codes_by_project(fi.project.uuid, pos.ext_code)
    for source in source_list:
        s_desc = "Cargo Ticket Nº-{} / TPV {} ({})".format(fi.id, pos.name, source)
        s_total = get_source_total(fi, source)
        cash_code = ""
        wh_write_log("------> Source: {} - Total: {}".format(source, s_total))
        print("------> Source: {} - Total: {}".format(source, s_total))
        send_charge(pwu,b_code,room_code,cont_name,cont_id,has_credit,limit_credit,source,s_desc,date,s_total*factor,cash_code)


#def send_charges_room(pwu, fi, guest, pos, factor):
#    booking_code = guest.ext_id
#    room_code = guest.room
#    contact_name = "{} {}".format(guest.name, guest.surname)
#    contact_id = guest.ext_id
#    has_credit = "true"
#    limit_credit = 0
#    s_drink = pos.code1
#    s_food = pos.code2
#    s_break = pos.code3
#    sd_drink = "Cargo Ticket Nº-{} / TPV {} (Bebidas)".format(fi.id, pos.name)
#    sd_food = "Cargo Ticket Nº-{} / TPV {} (Comidas)".format(fi.id, pos.name)
#    sd_break = "Cargo Ticket Nº-{} / TPV {} (Desayunos)".format(fi.id, pos.name)
#    date = fi.date.strftime("%Y-%m-%dT%H:%M:%S")
#    ta_drink = get_drinks_total(fi, None)
#    ta_food = get_food_total(fi, None)
#    ta_break = get_breakfast_total(fi, None)
#    cash_code = ""
#
#    if ta_drink != None:
#        #wh_write_log("------> BEBIDAS")
#        send_charge(pwu,booking_code,room_code,contact_name,contact_id,has_credit,limit_credit,s_drink,sd_drink,date,ta_drink*factor,cash_code)
#    if ta_food != None:
#        #wh_write_log("------> COMIDAS")
#        send_charge(pwu,booking_code,room_code,contact_name,contact_id,has_credit,limit_credit,s_food,sd_food,date,ta_food*factor,cash_code)
#    if ta_break != None:
#        #wh_write_log("------> DESAYUNO")
#        send_charge(pwu,booking_code,room_code,contact_name,contact_id,has_credit,limit_credit,s_break,sd_break,date,ta_break*factor,cash_code)
#
def send_charges_room(pwu, fi, guest, pos, factor):
    b_code = guest.ext_id
    room_code = guest.room
    cont_name = "{} {}".format(guest.name, guest.surname)
    cont_id = guest.ext_id
    has_credit = "true"
    limit_credit = 0
    source = "0900"
    s_desc = "Cargo Ticket Nº-{} / TPV {}".format(fi.id, pos.name)
    date = fi.date.strftime("%Y-%m-%dT%H:%M:%S")
    s_total = fi.get_total
    cash_code = ""

    #FIXME: el HotelSource tiene que ser el del club y no el del hotel
    #FIXME: el contactId tiene que venir de una consulta
    #wh_write_log("------> {}".format(source))
    send_charge(pwu,b_code,room_code,cont_name,cont_id,has_credit,limit_credit,source,s_desc,date,s_total*factor,cash_code)


