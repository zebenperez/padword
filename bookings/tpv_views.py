from django.contrib import auth
from django.shortcuts import render, redirect
from django.urls import reverse

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, reverse_cardkey
from web.models import Project, Waiter
from contents.models import Category, ShoppingCart, Item, PaymentType, PointOfSale
from guest.models import Guest, Wristband
from web.lock_lib import ShLock

from .common_lib import get_or_create_form_instance_tpv, user_in_group
from .models import Form, FormInstance, Status
from django.conf import settings


import datetime
import json
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

def tpv_access(request, project_uuid):
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
    return render(request, 'bookings/tpv/tpv-welcome.html', context)

def tpv_login_form(request):
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
            point_of_sales = PointOfSale.objects.filter(project_uuid=project.uuid)
            return render(request, "bookings/tpv/index.html", {'point_of_sales': point_of_sales,})
        else:
            form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=project.uuid).first()
            pos = get_or_none(PointOfSale, request.session["point_of_sale"])
            fi = get_or_create_form_instance_tpv(form, pos.uuid, request.user.username)
            cat_list = [item.category for item in pos.categories.all()]
            item_favorites = []
            for cat in cat_list:
                item_favorites += list(cat.get_items_favorites)
            item_commons = form.get_common_items()

            #template = request.GET["template"] if "template" in request.GET and request.GET["template"] != "" else "index"
            context = {
                'project_uuid':project.uuid, 
                'form':form, 
                'fi': fi, 
                'cat_list': cat_list,
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
        band = Wristband.objects.filter(code = reverse_cardkey(val), guest__deleted=False).first()
        regime = None
        if band != None and band.guest != None:
            gr = band.guest.regimes.first()
            regime = gr.regime if gr != None else None
        return render(request, "bookings/tpv/view-ticket.html", {'fi':fi, 'band': band, 'regime': regime})
        #return render(request, "bookings/tpv/view-guest-info.html", {'fi':fi, 'band': band, 'regime': regime})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})


#@group_required("waiters")
#def tpv_shopping_cart(request):
#    try:
#        #form_id = get_param(request.GET, "form_id", 0)
#        #form = get_or_none(Form, form_id)
#        fi = get_or_none(FormInstance, request.GET["fi_id"])
#        form = fi.form
#        category = form.get_category
#        item_favorites = []
#        pos = get_or_none(PointOfSale, request.session["point_of_sale"])
#        #fi = get_or_create_form_instance(form, pos.uuid, request.user.username)
#
#        for cat in category.get_active_childrens:
#            item_favorites += list(cat.get_items_favorites)
#
#        item_commons = form.get_common_items()
#
#        context = {'category':category, 'form': form, 'fi':fi, 'back': False, 'item_favorites': item_favorites, 'item_commons': item_commons}
#        return render(request, form.form_type.template, context)
#    except Exception as e:
#        print(e)
#        return render(request, "error_exception.html", {'exc':show_exc(e)})
#
#@group_required("waiters")
#def tpv_category_shopping_cart(request, form_id=None, cat_id = None):
#    try:
#        form_id = get_param(request.GET, "form_id", 0)
#        cat_id = get_param(request.GET, "cat_id")
#        guest = get_or_none(Guest, get_param(request.GET, "guest_id"))
#
#        instance = get_or_none(FormInstance, form_id)
#        category = Category.objects.get(uuid=cat_id)
#        form = Form.objects.filter(category=category.uuid).first()
#        return render(request, form.form_type.template, {'category':category, 'fi':instance, 'back': False, 'guest': guest})
#    except Exception as e:
#        print(e)
#        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_add_item(request):
    try:
        form_id = request.GET["form_id"]
        item_id = request.GET["item_id"]
        item = get_or_none(Item, int(item_id))

        obj = ShoppingCart(form_instance_id=int(form_id), item=item, comments='')
        obj.save()

        instance = FormInstance.objects.get(pk=form_id)
        return render(request, "bookings/tpv/view-ticket.html", {'fi':instance,})
        #items = instance.items_in_bookings(item).count()
        #return render(request, "bookings/tpv/show-instance-result.html", {'fi':instance,'item':item,'items':items})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

#@group_required("waiters")
#def tpv_remove_item(request):
#    try:
#        form_id = request.GET["form_id"]
#        item_id = request.GET["item_id"]
#        item = get_or_none(Item, int(item_id))
#        instance = FormInstance.objects.get(pk=form_id)
#        items = instance.items_in_bookings(item)
#        obj = items.last()
#        obj.delete()
#        return render(request, "bookings/tpv/view-ticket.html", {'fi':instance,})
#        #return render(request, "bookings/tpv/show-instance-result.html", {'fi':instance,'item':item,'items':items.count()})
#    except Exception as e:
#        print(e)
#        return render(request, "error_exception.html", {'exc':show_exc(e)})
#
#@group_required("waiters")
#def tpv_set_items(request):
#    try:
#        instance_id = get_param(request.GET, "form_id")
#        instance = FormInstance.objects.get(pk=instance_id)
#        items = ShoppingCart.objects.filter(form_instance_id=instance.pk)
#        return HttpResponse('{} art.&nbsp;&nbsp;&nbsp;{:.2f} &euro;'.format(items.count(), instance.get_total))
#    except Exception as e:
#        #return HttpResponse(show_exc(e))
#        return render(request, "error_exception.html", {'exc':show_exc(e)})
#
#@group_required("waiters")
#def tpv_order_view(request, par=None):
#    try:
#        project_uuid = get_param(request.GET, "project_uuid")
#        pos = get_or_none(PointOfSale, request.session["point_of_sale"])
#        fi_list = FormInstance.objects.filter(guest_uuid = pos.uuid, status_list__isnull = True) if pos != None else []
#        return render(request, "bookings/tpv/view-ticket.html", {'fi_list': fi_list})
#    except Exception as e:
#        print (show_exc(e))
#        return render(request, "error_exception.html", {'exc':show_exc(e)})
#
@group_required("waiters")
def tpv_order_remove(request):
    try:
        fi_id = request.GET["obj_id"]
        fi = FormInstance.objects.get(pk = fi_id)
        #project = fi.form.project
        form = fi.form
        fi.delete()
            
        pos = get_or_none(PointOfSale, request.session["point_of_sale"])
        fi = get_or_create_form_instance_tpv(form, pos.uuid, request.user.username)
        return render(request, "bookings/tpv/view-ticket.html", {'fi': fi})
        #context = {'msg': "05", "project_uuid": project.uuid}
        #return render(request, 'bookings/tpv/show-msg.html', context)
    except Exception as e:
        logger.error("[bookings-remove_fi] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("waiters")
def tpv_order_item_remove(request):
    try:
        item_id = request.GET["item_id"]
        obj = get_or_none(ShoppingCart, item_id)
        #item = obj.item
        fi = get_or_none(FormInstance, obj.form_instance_id)
        obj.delete()

        #pos = get_or_none(PointOfSale, request.session["point_of_sale"])
        #fi_list = FormInstance.objects.filter(guest_uuid = pos.uuid, status_list__isnull = True) if pos != None else []
        #total_items = FormInstance.get_all_items(guest)
        #total_items = 0
        return render(request, "bookings/tpv/view-ticket.html", {'fi':fi,})
        #return render(request, "bookings/tpv/view-ticket.html", {'fi_list':fi_list, 'item_refresh':item, 'total_items':total_items})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def tpv_order_item_comment(request):
    try:
        item_id = request.GET["item_id"]
        form_id = request.GET["form_id"]
        obj = get_or_none(ShoppingCart, int(item_id))

        return render(request, "bookings/tpv/shopping-form.html", {'obj':obj, 'form_id':form_id})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

#@group_required("waiters")
#def tpv_order_payment(request):
#    try:
#        fi_id = request.GET["obj_id"]
#        fi = get_or_none(FormInstance, fi_id)
#        context = {'fi': fi}
#        return render(request, 'bookings/tpv/view-payment-types.html', context)
#    except Exception as e:
#        print(e)
#        logger.error("[bookings-booking_send] {}".format(str(e)))
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})
#
@group_required("waiters")
def tpv_order_send(request):
    try:
        fi_id = get_param(request.GET, "obj_id")
        pt_id = get_param(request.GET, "payment_type", "")
        amount = get_param(request.GET, "amount", "")

        fi = get_or_none(FormInstance, fi_id)
        fi.set_status("01", request.user, "")
        fi.date = datetime.datetime.now()
        if pt_id != "":
            pt = get_or_none(PaymentType, pt_id)
            fi.payment_type = pt
            fi.amount = amount
        fi.save()
        context = {'msg': fi.get_status.status.code, 'project_uuid': fi.form.project.uuid}
        return render(request, 'bookings/tpv/show-msg.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-booking_send] {}".format(str(e)))
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
def tpv_close(request):
    auth.logout(request)
    project_uuid = request.GET["project_uuid"] if "project_uuid" in request.GET else ""
    return redirect(tpv_access, project_uuid)


