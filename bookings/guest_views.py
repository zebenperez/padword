from django.apps import apps
from django.contrib import auth
from django.db.models import Q
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, get_bool, new_ui_slug
from web.models import Device, Project
from contents.models import Category, ShoppingCart, Item
from guest.models import Guest

from .common_lib import get_or_create_form_instance, get_max_index, get_or_create_answer_instance, write_log, user_in_group
from .models import AnswerInstance, Field, Form, FormChannel, FormInstance, Question, Block, GuestUser

import datetime
import logging
logger = logging.getLogger(__name__)


#'''
#    Bookings shopping cart methods
#'''
#@group_required("admins", "projects", "guests")
#def item_to_shopping_cart(request):
#    try:
#        form_id = request.GET["form_id"]
#        item_id = request.GET["item_id"]
#        item = get_or_none(Item, int(item_id))
#
#        obj = ShoppingCart(form_instance_id=int(form_id), item=item, comments='')
#        obj.save()
#
#        instance = FormInstance.objects.get(pk=form_id)
#        items = ShoppingCart.objects.filter(form_instance_id=int(form_id), item=item)
#
#        total_price = "{:.2f}".format(instance.get_total)
#        total_items = ShoppingCart.objects.filter(form_instance_id=int(form_id)).count()
#
#        return render(request, "bookings/show-instance-result.html", {'items':items,'item':item,'total_price':total_price,'total_items':total_items})
#        #return HttpResponse('{} art.&nbsp;&nbsp;&nbsp;{:.2f} &euro;'.format(items.count(), instance.get_total))
#        #return render(request, "bookings/shopping-form.html", {'obj':obj})
#    except Exception as e:
#        return render(request, "error_exception.html", {'exc':show_exc(e)})
#
#@group_required("admins", "projects", "guests")
#def show_category_shopping_cart(request, form_id=None, cat_id = None):
#    try:
#        if not form_id:
#            form_id = request.GET["form_id"]
#        if not cat_id:
#            cat_id = request.GET["cat_id"]
#        instance = FormInstance.objects.get(pk=form_id)
#        category = Category.objects.get(uuid=cat_id)
#        return render(request, "bookings/shopping_cart.html", {'category':category, 'fi':instance})
#    except Exception as e:
#        return render(request, "error_exception.html", {'exc':show_exc(e)})
#
#@group_required("admins", "projects", "guests")
#def view_shopping_cart(request):
#    try:
#        instance_id = get_param(request.GET, "form_id")
#        instance = FormInstance.objects.get(pk=instance_id)
#        items = ShoppingCart.objects.filter(form_instance_id=instance.pk)
#        total_price = instance.get_total
#        return render(request, "bookings/view-shopping-cart.html", {'fi':instance, 'items':items, 'total':total_price})
#    except Exception as e:
#        return HttpResponse(show_exc(e))
#
#@group_required("admins", "projects", "guests")
#def get_price_shopping_cart(request):
#    try:
#        instance_id = get_param(request.GET, "form_id")
#        instance = FormInstance.objects.get(pk=instance_id)
#        items = ShoppingCart.objects.filter(form_instance_id=instance.pk)
#        return HttpResponse('{} art.&nbsp;&nbsp;&nbsp;{:.2f} &euro;'.format(items.count(), instance.get_total))
#    except Exception as e:
#        return HttpResponse(show_exc(e))
#
#@group_required("admins", "projects", "guests")
#def remove_item_from_shopping_cart(request):
#    try:
#        item_id = request.GET["item_id"]
#        obj = ShoppingCart.objects.get(pk=item_id)
#        instance_id = obj.form_instance_id
#        obj.delete()
#        instance = FormInstance.objects.get(pk=instance_id)
#        items = ShoppingCart.objects.filter(form_instance_id=instance.pk)
#        total_price = instance.get_total
#        return render(request, "bookings/view-shopping-cart.html", {'fi':instance, 'items':items, 'total':total_price})
#    except Exception as e:
#        return render(request, "error_exception.html", {'exc':show_exc(e)})
#
#@group_required("admins", "projects", "guests")
#def remove_generic_item_from_shopping_cart(request):
#    try:
#        form_id = request.GET["form_id"]
#        item_id = request.GET["item_id"]
#        item = get_or_none(Item, int(item_id))
#
#        items = ShoppingCart.objects.filter(form_instance_id=int(form_id), item=item)
#        counter = items.count() - 1
#        obj = items.last()
#        obj.delete()
#
#        instance = FormInstance.objects.get(pk=form_id)
#        total_price = "{:.2f}".format(instance.get_total)
#        total_items = ShoppingCart.objects.filter(form_instance_id=int(form_id)).count()
#
#        return render(request, "bookings/show-instance-result.html", {'items':items,'item':item,'total_price':total_price,'total_items':total_items})
#        #return render(request, "bookings/show-instance-result.html", {'items':items, 'item':item})
#        #return render(request, "bookings/view-shopping-cart.html", {'fi':instance, 'items':items, 'total':total_price})
#    except Exception as e:
#        return render(request, "error_exception.html", {'exc':show_exc(e)})
#

'''
    Bookings client methods
'''
def guest_access(request, form_uuid):
    device_imei = request.GET["device_imei"] if "device_imei" in request.GET else ""
    room_number = request.GET["room_number"] if "room_number" in request.GET else ""
    guest_name = request.GET["guest_name"] if "guest_name" in request.GET else ""
    guest_surname = request.GET["guest_surname"] if "guest_surname" in request.GET else ""
    context = {'form_uuid': form_uuid,'device_imei': device_imei,'room_number': room_number,'guest_name': guest_name,'guest_surname': guest_surname}
    return render(request, 'bookings/guest/guest-welcome.html', context)

def guest_access_bookings(request, project_uuid):
    next_url = reverse("my-bookings") if request.user.is_authenticated and user_in_group(request.user, "guests") else reverse("guest-form-login")
    context = {'project_uuid': project_uuid, 'next_url': next_url}
    return render(request, 'bookings/guest/guest-welcome.html', context)

def guest_form_login(request, form_uuid=None):
#def guest_form_login(request):
    try:
        if "form_uuid" in request.GET or form_uuid != None:
            form_uuid = request.GET["form_uuid"] if "form_uuid" in request.GET else form_uuid
            return render(request, 'guest_form_login.html', {'form_uuid': form_uuid})
        if "project_uuid" in request.GET:
            return render(request, 'guest_form_login.html', {'project_uuid': request.GET["project_uuid"]})
        return render(request, 'error_exception.html', {'exc': 'Form or project not found!'})
    except Exception as e:
        logger.error("[bookings-guest_form_login] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

def booking_new_guest(request):
    '''
        Guest access by form
    '''
    try:
        date = datetime.datetime.now()
        form_uuid = request.POST["form_uuid"]
        project_uuid = request.POST["project_uuid"]
        code = request.POST["code"]
        room = request.POST["room"]
        guest = Guest.objects.filter(Q(mobile=code) | Q(email=code)).filter(room=room, check_in__lte=date, check_out__gte=date).first()
        print (form_uuid, project_uuid)

        if guest == None:
            if form_uuid != "":
                return render(request, 'guest_form_login.html', {'form_uuid': form_uuid, 'error_msg':_('Sorry, your information is not right. Please, try again.')})
                #return render(request, "guest-error-login.html",  {'form_uuid':form_uuid})
            if project_uuid!= "":
                return redirect(reverse('guest-access-bookings', kwargs = {'project_uuid':project_uuid}))
            return render(request, 'error_exception.html', {'exc': 'Guest not found!'})
        if form_uuid != "":
            form = get_or_none(Form, form_uuid, "uuid")
            if form == None:
                return render(request, 'error_exception.html', {'exc': _('Form not found!')})
            if form.project == None:
                return render(request, 'error_exception.html', {'exc': _('Project not found!')})
            project = form.project
        else:
            project = get_or_none(Project, project_uuid, "uuid")
            if project == None:
                return render(request, 'error_exception.html', {'exc': _('Project not found!')})

        user, err = GuestUser.get_or_create_guest_user(guest.UUID, project.uuid, code)
        if err != "":
            return render(request, 'error_exception.html', {'exc': err})
        auth.login(request, user)

        return redirect(booking_new, form_uuid) if form_uuid != "" else redirect(bookings_by_guest, project.uuid)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-new_booking] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

#def booking_new_device(request, form_uuid):
def booking_new_device(request):
    '''
        Guest access by device
    '''
    try:
        form_uuid = request.GET["form_uuid"] if "form_uuid" in request.GET else ""
        device_imei = request.GET["device_imei"] if "device_imei" in request.GET else ""
        room_number = request.GET["room_number"] if "room_number" in request.GET else ""
        guest_name = request.GET["guest_name"] if "guest_name" in request.GET else ""
        guest_surname = request.GET["guest_surname"] if "guest_surname" in request.GET else ""

        if device_imei == "":
            return redirect(guest_form_login, form_uuid)
        device = get_or_none(Device, device_imei, "imei")
        if device == None:
            return redirect(guest_form_login, form_uuid)
        if device.room != room_number:
            return redirect(guest_form_login, form_uuid)
        guest = Guest.objects.filter(name=guest_name, surname=guest_surname, room=room_number).first()
        if guest == None:
            return redirect(guest_form_login, form_uuid)
        code = guest.get_code()
        if code == "":
            return render(request, 'error_exception.html', {'exc': _('Guest not found or not assigned to room number!')})
        form = get_or_none(Form, form_uuid, "uuid")
        if form == None:
            return render(request, 'error_exception.html', {'exc': _('Form not found!')})
        if form.project == None:
            return render(request, 'error_exception.html', {'exc': _('Project not found!')})

        user, err = GuestUser.get_or_create_guest_user(guest.UUID, form.project.uuid, code)
        if err != "":
            return render(request, 'error_exception.html', {'exc': err})
        auth.login(request, user)

        return redirect(booking_new, form_uuid)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-new_booking] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})
 
@group_required("admins", "projects", "guests")
def booking_new(request, form_uuid):
    '''
        Guest access by form
    '''
    try:
        form = get_or_none(Form, form_uuid, "uuid")
        if form == None:
            return render(request, 'error_exception.html', {'exc': _('Form not found!')})
        if form.project == None:
            return render(request, 'error_exception.html', {'exc': _('Project not found!')})

        gu = GuestUser.objects.filter(project_uuid=form.project.uuid, username=request.user.username).first()
        if gu == None or gu.guest == None:
            return render(request, 'error_exception.html', {'exc': 'User not found!'})

        fi = get_or_create_form_instance(form.uuid, gu.guest.UUID)
        write_log(request.user, fi, _("Booking created"))
        
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk)
        context = {'fi': fi, 'index': "0", "ro": False, 'items':items}
        return render(request, 'bookings/fillform.html', context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-new_booking] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
#def booking_send(request, fi_id):
def booking_send(request):
    try:
        fi_id = request.GET["obj_id"]
        fi = FormInstance.objects.get(pk = fi_id)
        previous_status = fi.status.name if fi.status != None else _("Created")
        fi.set_status("01")
        write_log(request.user, fi, _("Status change from {} to {}".format(previous_status, fi.status.name)))
        context = {'msg': fi.status.code, 'project_uuid': fi.form.project.uuid}
        return render(request, 'bookings/guest/show-msg.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-booking_send] {}".format(str(e)))
    return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
#def booking_remove(request, fi_id):
def booking_remove(request):
    try:
        fi_id = request.GET["obj_id"]
        fi = FormInstance.objects.get(pk = fi_id)
        project_uuid = fi.form.project.uuid if fi.form != None and fi.form.project != None else ""
        fi.delete()
        context = {'msg': "05", 'project_uuid': project_uuid}
        return render(request, 'bookings/guest/show-msg.html', context)
    except Exception as e:
        logger.error("[bookings-remove_fi] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects", "guests")
def bookings_by_guest(request, project_uuid=None):
#def bookings_by_guest(request):
    msg = ""
    try:
        if project_uuid == None:
            project_uuid = request.GET["project_uuid"]

        gu = GuestUser.objects.filter(project_uuid=project_uuid, username=request.user.username).first()
        if gu == None or gu.guest == None:
            return render(request, 'error_exception.html', {'exc': 'User not found!'})

        guest = gu.guest
        context = {
            'items': FormInstance.objects.filter(guest_uuid=guest.UUID, date__range=[guest.check_in, guest.check_out]),
            'guest': guest
        }
        return render (request, "bookings/guest/bookings-by-guest.html", context)
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
        msg = str(e)
        return render(request, 'error_exception.html', {'exc': str(e)})

@group_required("admins", "projects", "guests")
#def booking_view(request, fi_id):
def booking_view(request):
    try:
        fi_id = request.GET["obj_id"]
        fi = FormInstance.objects.get(pk = fi_id)
        form = get_or_none(Form, fi.form_uuid, 'uuid')
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk)

        #context = {'fi': fi, 'index': "0", "ro": True, 'items':items,}
        context = {'fi': fi, 'index': "0", 'project_uuid': form.project.uuid, 'items':items,}
        template = 'bookings/guest/view-booking-project.html' if fi.form.form_type.code == "ecom" else 'bookings/guest/view-booking.html'
        return render(request, template, context)
    except Exception as e:
        print(e)
        logger.error("[bookings-fill_form] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})
    return render(request, 'error_exception.html', {})

'''
    NOT USED BY MOMENT!!!
    Bookings remote methods
'''
@group_required("admins", "projects", "guests")
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

@group_required("admins", "projects", "guests")
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

@group_required("admins", "projects", "guests")
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

@group_required("admins", "projects", "guests")
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

@group_required("admins", "projects", "guests")
def autocomplete(request):
    model_name = request.GET["model"]
    field = request.GET["field"]
    value = request.GET["value"]
    html_id = request.GET["id"]

    model = apps.get_model("bookings", model_name)
    item_list = model.objects.filter(**{"{}__icontains".format(field): value})

    return render(request, 'bookings/autocomplete_field.html', {'item_list': item_list, 'id': html_id})

@group_required("admins", "projects", "guests")
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

@group_required("admins", "projects", "guests")
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

@group_required("admins", "projects", "guests")
def select_item(request):
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

            answer_name = "question_%s_field_%s_%s" % (q.id, f.id, index)
            context = {
                'fi_id': fi.id, 
                'q_id': q.id, 
                'f': f,
                'index': index, 
                'answer_name': answer_name, 
                'item_list': fi.form.get_category_items(),
                'value': ai.text
            }
        return render(request, "bookings/items-shop-field.html", context)
    except Exception as e:
        print(e)
        logger.error("[bookings-autosave]: {}".format(e))
        return render(request, 'error_exception.html', {'msg': str(e)})


'''
    Bookings shopping cart methods
'''
@group_required("admins", "projects", "guests")
def item_to_shopping_cart(request):
    try:
        form_id = request.GET["form_id"]
        item_id = request.GET["item_id"]
        item = get_or_none(Item, int(item_id))

        obj = ShoppingCart(form_instance_id=int(form_id), item=item, comments='')
        obj.save()

        instance = FormInstance.objects.get(pk=form_id)
        items = ShoppingCart.objects.filter(form_instance_id=int(form_id), item=item)

        total_price = "{:.2f}".format(instance.get_total)
        total_items = ShoppingCart.objects.filter(form_instance_id=int(form_id)).count()

        return render(request, "bookings/show-instance-result.html", {'items':items,'item':item,'total_price':total_price,'total_items':total_items})
        #return HttpResponse('{} art.&nbsp;&nbsp;&nbsp;{:.2f} &euro;'.format(items.count(), instance.get_total))
        #return render(request, "bookings/shopping-form.html", {'obj':obj})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
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

@group_required("admins", "projects", "guests")
def item_shopping_cart_comment(request):
    try:
        item_id = request.GET["item_id"]
        form_id = request.GET["form_id"]
        obj = get_or_none(ShoppingCart, int(item_id))

        return render(request, "bookings/shopping-form.html", {'obj':obj, 'form_id':form_id})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def view_shopping_cart(request):
    try:
        instance_id = get_param(request.GET, "form_id")
        instance = FormInstance.objects.get(pk=instance_id)
        items = ShoppingCart.objects.filter(form_instance_id=instance.pk)
        total_price = instance.get_total
        return render(request, "bookings/view-shopping-cart.html", {'fi':instance, 'items':items, 'total':total_price})
    except Exception as e:
        return HttpResponse(show_exc(e))

@group_required("admins", "projects", "guests")
def get_price_shopping_cart(request):
    try:
        instance_id = get_param(request.GET, "form_id")
        instance = FormInstance.objects.get(pk=instance_id)
        items = ShoppingCart.objects.filter(form_instance_id=instance.pk)
        return HttpResponse('{} art.&nbsp;&nbsp;&nbsp;{:.2f} &euro;'.format(items.count(), instance.get_total))
    except Exception as e:
        return HttpResponse(show_exc(e))

@group_required("admins", "projects", "guests")
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

@group_required("admins", "projects", "guests")
def remove_generic_item_from_shopping_cart(request):
    try:
        form_id = request.GET["form_id"]
        item_id = request.GET["item_id"]
        item = get_or_none(Item, int(item_id))

        items = ShoppingCart.objects.filter(form_instance_id=int(form_id), item=item)
        counter = items.count() - 1
        obj = items.last()
        obj.delete()

        instance = FormInstance.objects.get(pk=form_id)
        total_price = "{:.2f}".format(instance.get_total)
        total_items = ShoppingCart.objects.filter(form_instance_id=int(form_id)).count()

        return render(request, "bookings/show-instance-result.html", {'items':items,'item':item,'total_price':total_price,'total_items':total_items})
        #return render(request, "bookings/show-instance-result.html", {'items':items, 'item':item})
        #return render(request, "bookings/view-shopping-cart.html", {'fi':instance, 'items':items, 'total':total_price})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

def close(request):
    return render(request, "close-window.html")
