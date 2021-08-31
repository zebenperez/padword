from django.apps import apps
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, get_bool, new_ui_slug
from web.models import Device
from contents.models import Category, ShoppingCart, Item
from guest.models import Guest

from .common_lib import get_or_create_form_instance, get_max_index, get_or_create_answer_instance, write_log
from .models import AnswerInstance, Field, Form, FormChannel, FormInstance, Question, Block

import logging
logger = logging.getLogger(__name__)


'''
    Bookings shopping cart methods
'''
#@login_required
def item_to_shopping_cart(request):
    try:
        form_id = request.GET["form_id"]
        item_id = request.GET["item_id"]
        item = get_or_none(Item, int(item_id))

        obj = ShoppingCart(form_instance_id=int(form_id), item=item, comments='')
        obj.save()

        instance = FormInstance.objects.get(pk=form_id)
        items = ShoppingCart.objects.filter(form_instance_id=int(form_id), item=item)
        return render(request, "bookings/show-instance-result.html", {'items':items, 'item':item})
        return HttpResponse('{} art.&nbsp;&nbsp;&nbsp;{:.2f} &euro;'.format(items.count(), instance.get_total))
        #return render(request, "bookings/shopping-form.html", {'obj':obj})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

#@login_required
def show_category_shopping_cart(request, form_id=None, cat_id = None):
    try:
        if not form_id:
            form_id = request.GET["form_id"]
        if not cat_id:
            cat_id = request.GET["cat_id"]
        instance = FormInstance.objects.get(pk=form_id)
        category = Category.objects.get(uuid=cat_id)
        return render(request, "bookings/shopping_cart.html", {'category':category, 'fi':instance})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

#@login_required
def view_shopping_cart(request):
    try:
        instance_id = get_param(request.GET, "form_id")
        instance = FormInstance.objects.get(pk=instance_id)
        items = ShoppingCart.objects.filter(form_instance_id=instance.pk)
        total_price = instance.get_total
        return render(request, "bookings/view-shopping-cart.html", {'fi':instance, 'items':items, 'total':total_price})
    except Exception as e:
        return HttpResponse(show_exc(e))

#@login_required
def get_price_shopping_cart(request):
    try:
        instance_id = get_param(request.GET, "form_id")
        instance = FormInstance.objects.get(pk=instance_id)
        items = ShoppingCart.objects.filter(form_instance_id=instance.pk)
        return HttpResponse('{} art.&nbsp;&nbsp;&nbsp;{:.2f} &euro;'.format(items.count(), instance.get_total))
    except Exception as e:
        return HttpResponse(show_exc(e))

@login_required
def remove_item_from_shopping_cart(request):
    try:
        item_id = request.GET["item_id"]
        obj = ShoppingCart.objects.get(pk=item_id)
        instance_id = obj.form_instance_id
        obj.delete()
        instance = FormInstance.objects.get(pk=instance_id)
        items = ShoppingCart.objects.filter(form_instance_id=instance.pk)
        total_price = instance.get_total
        return render(request, "bookings/view-shopping-cart.html", {'fi':instance, 'items':items, 'total':total_price})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@login_required
def remove_generic_item_from_shopping_cart(request):
    try:
        form_id = request.GET["form_id"]
        item_id = request.GET["item_id"]
        item = get_or_none(Item, int(item_id))

        items = ShoppingCart.objects.filter(form_instance_id=int(form_id), item=item)
        counter = items.count() - 1
        obj = items.last()
        obj.delete()

        return render(request, "bookings/show-instance-result.html", {'items':items, 'item':item})
        return render(request, "bookings/view-shopping-cart.html", {'fi':instance, 'items':items, 'total':total_price})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


'''
    Bookings guest login
'''
def guest_login(request):
    return render(request, 'guest_login.html', {})

def guest_auth_login(request):
    return render(request, 'guest_login.html', {})

'''
    Bookings client methods
'''
#@login_required
#def booking_new(request, form_uuid, device_imei, room_number, guest_name, guest_surname):
def booking_new(request, form_uuid):
    try:
        form = get_or_none(Form, form_uuid, "uuid")
        if form == None:
            return render(request, 'error_exception.html', {'exc': _('Form not found!')})
        
        device_imei = request.GET["device_imei"] if "device_imei" in request.GET else ""
        room_number = request.GET["room_number"] if "room_number" in request.GET else ""
        guest_name = request.GET["guest_name"] if "guest_name" in request.GET else ""
        guest_surname = request.GET["guest_surname"] if "guest_surname" in request.GET else ""

        if device_imei == "":
            #return render(request, 'error_exception.html', {'exc': _('Device not found!')})
            return redirect(guest_login)
        device = get_or_none(Device, device_imei, "imei")
        if device == None:
            #return render(request, 'error_exception.html', {'exc': _('Device not found!')})
            return redirect(guest_login)
        if device.room != room_number:
            #return render(request, 'error_exception.html', {'exc': _('Device not assigned to room number!')})
            return redirect(guest_login)
        guest = Guest.objects.filter(name=guest_name, surname=guest_surname, room=room_number).first()
        if guest == None:
            #return render(request, 'error_exception.html', {'exc': _('Guest not found or not assigned to room number!')})
            return redirect(guest_login)

        fi = get_or_create_form_instance(form.uuid, device.uuid, room_number, guest_name, guest_surname)
        write_log(request.user, fi, _("Booking created"))
        
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk)
        context = {'fi': fi, 'index': "0", "ro": False, 'items':items}
        return render(request, 'bookings/fillform.html', context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-new_booking] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

#@group_required("admins", "projects", "clients")
def booking_send(request, fi_id):
    try:
        fi = FormInstance.objects.get(pk = fi_id)
        previous_status = fi.status.name if fi.status != None else _("Created")
        fi.set_status("01")
        write_log(request.user, fi, _("Status change from {} to {}".format(previous_status, fi.status.name)))
        context = {'msg': fi.status, 'device_uuid': fi.device_uuid}
        return render(request, 'bookings/show_msg.html', context)
    except Exception as e:
        logger.error("[bookings-booking_send] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

#@group_required("admins", "projects", "clients")
def booking_remove(request, fi_id):
    try:
        fi = FormInstance.objects.get(pk = fi_id)
        device_uuid = fi.device_uuid
        fi.delete()
        context = {'msg': "Cancelada", 'device_uuid': device_uuid}
        return render(request, 'bookings/show_msg.html', context)
    except Exception as e:
        logger.error("[bookings-remove_fi] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

#@group_required("admins", "projects", "clients")
def bookings_by_device(request, device_uuid):
    msg = ""
    try:
        device = get_or_none(Device, device_uuid, "uuid")
        if device != None:
            guest_list = Guest.current_by_room_project(device.room, device.project_uuid) 
            if len(guest_list) == 1:
                guest = guest_list[0]
                context = {
                    'items': FormInstance.objects.filter(device_uuid=device_uuid, date__range=[guest.check_in, guest.check_out]),
                    'guest': guest
                }
                return render (request, "bookings/bookings-by-device.html", context)
            else:
                msg = _("More than one guest at same time!") if len(guest_list) > 0 else _("Guest not found!")
        else:
            msg = _("Device not found!")
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
        msg = str(e)
    return render(request, 'error_exception.html', {'exc': msg})

'''
    NOT USED BY MOMENT!!!
    Bookings remote methods
'''
@login_required
def get_block(request):
    try:
        fi = get_or_none(FormInstance, request.GET["fi_id"])
        block = get_or_none(Block, request.GET["obj_id"])
        ro = get_bool(request.GET["ro"])
        if fi != None and block != None:
            context = { 'fi': fi, 'b': block, 'index': "0", "ro": ro}
            return render(request, 'bookings/block_form.html', context)
    except Exception as e:
        logger.error("[bookings-get_block] {}".format(str(e)))
        return render(request, 'error_exception.html', {'msg': str(e)})

@login_required
def new_row(request):
    try:
        fi = get_or_none(FormInstance, request.GET["fi_id"])
        q = get_or_none(Question, request.GET["obj_id"])
        max_index = get_max_index(q, fi)
        if fi != None and q != None and max_index <= q.max_answers:
            context = { 'fi': fi, 'q': q, 'index': (max_index + 1), 'ro': True}
            return render(request, 'bookings/question_row.html', context)
    except Exception as e:
        logger.error("[bookings-get_block] {}".format(str(e)))
        return render(request, 'error_exception.html', {'msg': str(e)})

@login_required
def remove_row(request):
    try:
        fi = get_or_none(FormInstance, request.GET["fi_id"])
        q = get_or_none(Question, request.GET["obj_id"])
        index = request.GET["index"]
        if fi != None and q != None:
            ai_list = AnswerInstance.objects.filter(form_instance=fi, question=q, index=index)
            for ai in ai_list:
                ai.delete()
            return HttpResponse('{"error": "false", "msg": "Saved!", "b_id": "%s", "q_id": "%s"}' % (q.block.id, q.id,))
    except Exception as e:
        logger.error("[bookings-get_block] {}".format(str(e)))
        return render(request, 'error_exception.html', {'msg': str(e)})

@login_required
def autosave_form_field(request):
    try:
        fi = get_or_none(FormInstance, request.GET["fi"])
        q = get_or_none(Question, request.GET["question"])
        f = get_or_none(Field, request.GET["field"])
        index = request.GET["index"]
        value = request.GET["value"]

        ai = get_or_create_answer_instance(fi, q, f, index)
        if ai != None:
            ai.text = value
            ai.save()
            return HttpResponse('{"error": "false", "msg": "Saved!", "b_id": "%s", "q_id": "%s"}' % (q.block.id, q.id))
        return HttpResponse("{'error': 'true', 'msg': 'Not saved, object not found!'}")
    except Exception as e:
        print(e)
        logger.error("[bookings-autosave]: {}".format(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

@login_required
def autocomplete(request):
    model_name = request.GET["model"]
    field = request.GET["field"]
    value = request.GET["value"]
    html_id = request.GET["id"]

    model = apps.get_model("bookings", model_name)
    item_list = model.objects.filter(**{"{}__icontains".format(field): value})

    return render(request, 'bookings/autocomplete_field.html', {'item_list': item_list, 'id': html_id})

@login_required
def autoupload(request):
    try:
        fi = get_or_none(FormInstance, request.POST["fi"])
        q = get_or_none(Question, request.POST["question"])
        f = get_or_none(Field, request.POST["field"])
        index = request.POST["index"]
        document = request.FILES['file']

        ai = get_or_create_answer_instance(fi, q, f, index)
        if ai != None:
            ai.text = document.name
            ai.document = document
            ai.save()
            answer_name = "question_%s_field_%s_%s" % (q.id, f.id, index)
            context = {
                'fi_id': fi.id, 
                'q_id': q.id, 
                'f': f,
                'index': index, 
                'answer_name': answer_name, 
                'doc': ai.document,
            }
        return render(request, "bookings/file_field.html", context)
    except Exception as e:
        print(e)
        logger.error("[bookings-autosave]: {}".format(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

@login_required
def remove_file(request):
    try:
        fi = get_or_none(FormInstance, request.GET["fi"])
        q = get_or_none(Question, request.GET["question"])
        f = get_or_none(Field, request.GET["field"])
        index = request.GET["index"]

        ai = get_or_create_answer_instance(fi, q, f, index)
        if ai != None:
            ai.document.delete(save=False)
            ai.document = None
            ai.text = ""
            ai.save()

            answer_name = "question_%s_field_%s_%s" % (q.id, f.id, index)
            context = {
                'fi_id': fi.id, 
                'q_id': q.id, 
                'f': f,
                'index': index, 
                'answer_name': answer_name, 
                'doc': ai.document,
            }
        return render(request, "bookings/file_field.html", context)
    except Exception as e:
        print(e)
        logger.error("[bookings-autosave]: {}".format(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

