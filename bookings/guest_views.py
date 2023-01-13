from django.apps import apps
from django.contrib import auth
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 
from django.views.i18n import check_for_language
from django.utils import translation

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, get_bool, new_ui_slug
from web.models import Device, Project, ProjectUser, Lock
from contents.models import Category, ShoppingCart, Item, PaymentType
from guest.models import Guest, GuestNotification
from web.lock_lib import ShLock

from .common_lib import get_or_create_form_instance, get_max_index, get_or_create_answer_instance, user_in_group, get_guest, get_login_template
from .models import AnswerInstance, Field, Form, FormChannel, FormInstance, Question, Block, GuestUser, Status
from django.conf import settings


import datetime
import json
import logging
logger = logging.getLogger(__name__)

'''
    Bookings client methods
'''
#def check_user(user, form_uuid="", project_uuid=""):
#    if not user.is_authenticated:
#        return False
#    if not user_in_group(user, "guests"):
#        return False
#    if form_uuid != "":
#        form = get_or_none(Form, form_uuid, "uuid")
#        if form == None or form.project == None:
#            return False
#        project_uuid = form.project.uuid
#    if project_uuid == "":
#        return False
#
#    guest = Guest.check_valid_booking(project_uuid, user.username)
#    if guest == None:
#        return False
#
#    return True

def check_user(user, guest):
    if not user.is_authenticated:
        return False
    if not user_in_group(user, "guests"):
        return False
    if guest == None:
        return False
    if not guest.have_valid_booking():
        return False
    return True

def guest_access(request, category_uuid):
    cat = get_or_none(Category, category_uuid, "uuid")
    context = {'project_uuid': cat.project.uuid, 'cat': cat}
    guest = get_guest(request.user.username, cat.project.uuid)
    #if check_user(request.user, project_uuid=cat.project.uuid):
    if check_user(request.user, guest):
        next_url = reverse("pwa-index-cat", kwargs = {'category_uuid':category_uuid})
        #guest = Guest.check_valid_booking(cat.project.uuid, request.user.username)
        context["guest"] = guest
    else:
        auth.logout(request)
        next_url = reverse("guest-form-login")
    context["next_url"] = next_url
    return render(request, 'bookings/guest/guest-welcome.html', context)

def guest_access_anonymous(request, category_uuid):
    try:
        cat = get_or_none(Category, category_uuid, "uuid")
        guest = Guest.check_valid_booking(cat.project.uuid, "611111111", "1234")

        user, err = GuestUser.get_or_create_guest_user(guest.UUID, cat.project.uuid, guest.id)
        if err != "":
            return render(request, 'error_exception.html', {'exc': err})
        auth.login(request, user)

        context = {'project_uuid': cat.project.uuid, 'cat': cat}
        if check_user(request.user, guest):
            next_url = reverse("pwa-index-cat", kwargs = {'category_uuid':category_uuid})
            context["guest"] = guest
            context["next_url"] = next_url
            return render(request, 'bookings/guest/guest-welcome.html', context)
        err = "User not valid"
    except Exception as e:
        print(e)
        err = show_exc(e)
    return render(request, 'error_exception.html', {'exc':err})
 

def guest_form_login(request):
    try:
        if "project_uuid" in request.GET:
            cat_uuid = request.GET["category_uuid"] if "category_uuid" in request.GET else ""
            error = request.GET["error"] if "error" in request.GET else ""
            return render(request, get_login_template(cat_uuid), {'project_uuid':request.GET["project_uuid"],'category_uuid':cat_uuid,'error':error})
            #return render(request, 'guest_form_login.html', {'project_uuid': request.GET["project_uuid"], 'category_uuid': cat_uuid, 'error': error})
        return render(request, 'error_exception.html', {'exc': 'Form or project not found!', 'error-msg': 'Form or project not found!'})
    except Exception as e:
        logger.error("[bookings-guest_form_login] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

def booking_new_guest(request):
    '''
        Guest access by form
    '''
    try:
        project_uuid = request.POST["project_uuid"]
        category_uuid = request.POST["category_uuid"]
        code = request.POST["code"]
        room = request.POST["room"]
        lang = request.POST["lang"] if "lang" in request.POST else ""

        if code == "" or room == "":
            err = _('You must to complete username and password!')
            return render(request, get_login_template(category_uuid), {'project_uuid': project_uuid, 'category_uuid': category_uuid, 'error': err})

        project = get_or_none(Project, project_uuid, "uuid")
        if project == None:
            guests = Guest.objects.filter(email = code)
            projects = [guest.project for guest in guests]
        else:
            projects = [project]

        guest = None
        for project in projects:
            guest = Guest.check_valid_booking(project.uuid, code, room)
            if guest != None:
                break

        if guest == None:
            return render(request, 'guest-error-login.html', {'project_uuid': project_uuid, 'category_uuid': category_uuid})

        user, err = GuestUser.get_or_create_guest_user(guest.UUID, project.uuid, guest.id)
        if err != "":
            return render(request, 'error_exception.html', {'exc': err})
        auth.login(request, user)

        if lang != "":
            guest.language = lang
            guest.save()
            return redirect(reverse("pwa-index-cat", kwargs = {'category_uuid':category_uuid, 'lang': lang}))
        
        return redirect(reverse("pwa-index-cat", kwargs = {'category_uuid':category_uuid}))
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-new_booking] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def booking_send(request):
    try:
        #fi_id = request.GET["obj_id"]
        #fi = FormInstance.objects.get(pk = fi_id)
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
        context = {'msg': fi.get_status.status.code}
        return render(request, 'bookings/guest/show-msg.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-booking_send] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def booking_remove(request):
    try:
        fi_id = request.GET["obj_id"]
        fi = FormInstance.objects.get(pk = fi_id)
        fi.delete()
        context = {'msg': "05"}
        return render(request, 'bookings/guest/show-msg.html', context)
    except Exception as e:
        logger.error("[bookings-remove_fi] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def booking_payment_type(request):
    try:
        fi_id = request.GET["obj_id"]
        fi = get_or_none(FormInstance, fi_id)
        context = {'fi': fi}
        return render(request, 'bookings/ecom/view-payment-types.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-booking_send] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def bookings_by_guest(request, project_uuid=None):
    msg = ""
    try:
        if project_uuid == None:
            project_uuid = request.GET["project_uuid"]

        guest = get_guest(request.user.username, project_uuid)
        if guest == None:
            return render(request, 'error_exception.html', {'exc': 'User not found!'})

        cat_uuid = request.GET["cat_id"] if "cat_id" in request.GET else ""
        context = {
            'items': FormInstance.objects.filter(guest_uuid=guest.UUID, date__range=[guest.check_in, guest.check_out], status_list__isnull=False).distinct(),
            'status_list': Status.objects.all(),
            'cat_uuid': cat_uuid,
            'guest': guest
        }
        return render (request, "bookings/guest/bookings-by-guest.html", context)
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
        msg = str(e)
        return render(request, 'error_exception.html', {'exc': str(e)})

@group_required("admins", "projects", "guests")
def booking_view(request):
    try:
        fi_id = request.GET["obj_id"]
        fi = FormInstance.objects.get(pk = fi_id)
        #form = get_or_none(Form, fi.form_uuid, 'uuid')
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk)

        cat_uuid = request.GET["cat_id"] if "cat_id" in request.GET else ""
        context = {'fi': fi, 'index': "0", 'project_uuid': fi.form.project.uuid, 'items':items, 'cat_uuid': cat_uuid}
        return render(request, 'bookings/guest/view-booking.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-fill_form] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

'''
    Notifications
'''
@group_required("admins", "projects", "guests")
def notifications_by_guest(request, project_uuid=None):
    msg = ""
    try:
        cat_uuid = request.GET["cat_id"] if "cat_id" in request.GET else ""
        cat = get_or_none(Category, cat_uuid, "uuid")
        if cat == None:
            return render(request, 'error_exception.html', {'exc': 'Category not found!'})

        guest = get_guest(request.user.username, cat.project_uuid)
        if guest == None:
            return render(request, 'error_exception.html', {'exc': 'User not found!'})
                    
        guest.check_all_notifications()
        return render (request, "bookings/guest/notifications-by-guest.html", {'guest': guest, 'cat_uuid': cat.uuid})
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
        msg = str(e)
        return render(request, 'error_exception.html', {'exc': str(e)})

@group_required("admins", "projects", "guests")
def notification_view(request):
    try:
        gn = get_or_none(GuestNotification, request.GET["obj_id"])
        if gn != None:
            gn.read = True
            gn.save()
        return render(request, "bookings/guest/notification-view.html", {'item': gn})
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc': str(e)})

@group_required("admins", "projects", "guests")
def notifications_not_readed(request):
    guest = get_or_none(Guest, request.GET["obj_id"])
    guest.check_all_notifications()
    return HttpResponse("{}".format(guest.get_not_read_notifications()))

@group_required("admins", "projects", "guests")
def notifications_check(request, project_uuid=None):
    try:
        guest = get_or_none(Guest, request.GET["obj_id"])
        if guest == None:
            return render(request, 'error_exception.html', {'exc': 'User not found!'})

        guest.check_all_notifications()
        return render (request, "bookings/guest/notification-list.html", {'guest': guest})
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc': str(e)})


'''
    Messages
'''
@group_required("admins", "projects", "guests")
def messages_by_guest(request, project_uuid=None):
    msg = ""
    try:
        if project_uuid == None:
            project_uuid = request.GET["project_uuid"]

        guest = get_guest(request.user.username, project_uuid)
        if guest == None:
            return render(request, 'error_exception.html', {'exc': 'User not found!'})

        return render(request, "bookings/guest/messages-by-guest.html", {'guest': guest, 'messages': guest.get_messages(True), 'guest_msg': 'True'})
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
        msg = str(e)
        return render(request, 'error_exception.html', {'exc': str(e)})


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

    return render(request, 'bookings/general/autocomplete_field.html', {'item_list': item_list, 'id': html_id})

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
        guest = get_or_none(Guest, get_param(request.GET, "guest_id"))
        index = request.GET["index"]
        value = request.GET["value"]
        add = request.GET["add"] if "add" in request.GET else ""

        ai = get_or_create_answer_instance(fi, q, f, index)
        if ai != None:
            if value == "" or "-" in value:
                ai.text = "{}|".format(value)
            else:
                if add == "False":
                    ai.text = ai.text.replace("{}|".format(value), "")
                else:
                    if "{}|".format(value) not in ai.text:
                        ai.text += "{}|".format(value)
            ai.save()

            answer_name = "question_%s_field_%s_%s" % (q.id, f.id, index)
            context = {
                'guest': guest, 
                'fi_id': fi.id, 
                'q_id': q.id, 
                'f': f,
                'index': index, 
                'answer_name': answer_name, 
                'item_list': fi.form.get_category_items(),
                'selected_item': ai.get_item() if ai != None else None,
                'value': ai.text
            }
        return render(request, "bookings/ecom/items-shop-field.html", context)
    except Exception as e:
        print(e)
        logger.error("[bookings-autosave]: {}".format(e))
        #return render(request, 'error_exception.html', {'msg': str(e)})
        return render(request, 'error_exception.html', {'msg': _("Sorry, there was a problem with your booking, please try again!")})


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
        items = instance.items_in_bookings(item).count()
        return render(request, "bookings/ecom/show-instance-result.html", {'fi':instance,'item':item,'items':items})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def show_category_shopping_cart(request, form_id=None, cat_id = None):
    try:
        form_id = get_param(request.GET, "form_id", 0)
        cat_id = get_param(request.GET, "cat_id")
        guest = get_or_none(Guest, get_param(request.GET, "guest_id"))

        instance = get_or_none(FormInstance, form_id)
        category = Category.objects.get(uuid=cat_id)
        form = Form.objects.filter(category=category.uuid).first()
        return render(request, form.form_type.template, {'category':category, 'fi':instance, 'back': False, 'guest': guest})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def item_shopping_cart_comment(request):
    try:
        item_id = request.GET["item_id"]
        form_id = request.GET["form_id"]
        obj = get_or_none(ShoppingCart, int(item_id))

        return render(request, "bookings/ecom/shopping-form.html", {'obj':obj, 'form_id':form_id})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def view_shopping_cart(request, par=None):
    try:
        project_uuid = get_param(request.GET, "project_uuid")
        guest = get_guest(request.user.username, project_uuid)
        fi_list = FormInstance.objects.filter(guest_uuid = guest.UUID, status_list__isnull = True) if guest != None else []
        return render(request, "bookings/ecom/view-shopping-cart.html", {'fi_list': fi_list})
    except Exception as e:
        print (show_exc(e))
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def get_price_shopping_cart(request):
    try:
        instance_id = get_param(request.GET, "form_id")
        instance = FormInstance.objects.get(pk=instance_id)
        items = ShoppingCart.objects.filter(form_instance_id=instance.pk)
        return HttpResponse('{} art.&nbsp;&nbsp;&nbsp;{:.2f} &euro;'.format(items.count(), instance.get_total))
    except Exception as e:
        #return HttpResponse(show_exc(e))
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def remove_item_from_shopping_cart(request):
    try:
        item_id = request.GET["item_id"]
        obj = ShoppingCart.objects.get(pk=item_id)
        item = obj.item
        obj.delete()

        guest = get_guest(request.user.username, item.project.uuid)
        fi_list = FormInstance.objects.filter(guest_uuid = guest.UUID, status_list__isnull = True) if guest != None else []
        total_items = FormInstance.get_all_items(guest)
        return render(request, "bookings/ecom/view-shopping-cart.html", {'fi_list':fi_list, 'item_refresh':item, 'total_items':total_items})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def remove_generic_item_from_shopping_cart(request):
    try:
        form_id = request.GET["form_id"]
        item_id = request.GET["item_id"]
        item = get_or_none(Item, int(item_id))
        instance = FormInstance.objects.get(pk=form_id)
        items = instance.items_in_bookings(item)
        obj = items.last()
        obj.delete()

        return render(request, "bookings/ecom/show-instance-result.html", {'fi':instance,'item':item,'items':items.count()})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

'''
    Bookings menu
'''
@group_required("admins", "projects", "guests")
def show_category_menu(request, cat_id=None, back="True"):
    try:
        if not cat_id:
            cat_id = request.GET["cat_id"] if "cat_id" in request.GET else 0
        category = get_or_none(Category, cat_id, "uuid")

        fi = None
        form = Form.objects.filter(category=category.uuid).first()
        guest = get_guest(request.user.username, category.project_uuid)
        fi = get_or_create_form_instance(form, guest.UUID) if guest != None else None
        items = FormInstance.get_all_items(guest)

        return render(request, form.form_type.template, {'category':category,'form':form,'fi':fi,'index':0,'items':items,'guest':guest,'back': back})
    except Exception as e:
        print(show_exc(e))
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def show_key_menu(request):
    try:
        cat_id = request.GET["cat_id"] if "cat_id" in request.GET else 0
        category = get_or_none(Category, cat_id, "uuid")
        guest = get_guest(request.user.username, category.project_uuid)

        return render(request, 'bookings/menus/menu_keys_inner.html', {'category':category, 'guest':guest,})
    except Exception as e:
        print(show_exc(e))
        return render(request, "error_exception.html", {'exc':show_exc(e)})


'''
    Bookings items
'''
@group_required("admins", "projects", "guests")
def show_item(request):
    try:
        guest_id = request.GET["guest_id"] if "guest_id" in request.GET else ""
        item_id = request.GET["item_id"]
        guest = get_or_none(Guest, int(guest_id)) if guest_id != "" else None
        item = get_or_none(Item, int(item_id))

        print("--1-")
        return render(request, "bookings/show-item-details.html", {'item':item, 'guest': guest})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})


def close(request):
    return render(request, "close-window.html")

@group_required("admins", "projects", "guests")
def close_window(request):
    auth.logout(request)
    cat_uuid = request.GET["category_uuid"] if "category_uuid" in request.GET else ""
    return redirect(guest_access, cat_uuid)

@group_required("admins", "projects", "guests")
def guest_notifications(request, form_id):
    try:
        form = get_or_none(Form, form_id)
        #gu = GuestUser.objects.filter(project_uuid=form.project.uuid, username=request.user.username).first()
        guest = get_guest(request.user.username, form.project.uuid)
        bookings = FormInstance.objects.filter(guest_uuid=guest.UUID, status_list__read=False).order_by('pk')
        val = ""
        if len(bookings) > 0:
            #val = _("You have some news in your orders:\n")
            for booking in bookings:
                val += _("- Order {} with current status {}\n".format(booking.form.get_category.name, booking.get_status.status.name))
        val += _("- Not readed notifications -> {}".format(guest.get_not_read_notifications()))
        result = {"title": "{}".format(_("You have some news\n")), "text": val}
        return HttpResponse(json.dumps(result))
    except Exception as e:
        logger.error("[bookings-new_booking] {}".format(str(e)))
        print(e)
        return HttpResponse("")

@group_required("admins", "projects", "guests")
def set_guest_language(request):
    try:
        category_uuid = get_param(request.GET, "cat_id")
        lang = get_param(request.GET, "lang")
        category = get_or_none(Category, category_uuid, "uuid")
        guest = get_guest(request.user.username, category.project_uuid)
        guest.language = lang
        guest.save()

        form = Form.objects.filter(category__in = [category.uuid]).first()
        context = {'form': form, 'project_uuid': category.project.uuid, 'guest': guest}
        translation.activate(lang)
        response = render(request, form.form_type.template_base, context)
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
        return response
    except Exception as e:
        #print (show_exc(e))
        return render(request, 'error_exception.html', {'exc': show_exc(e), 'error-msg': show_exc(e)})

'''
    Open Locks
'''
#@group_required("admins", "projects", "guests")
@group_required("guests")
def open_lock(request):
    lock = get_or_none(Lock, request.GET["obj_id"])
    guest = get_guest(request.user.username, lock.project.uuid)
    msg = False
    if guest != None and guest.can_open_lock(lock):
        msg = lock.open_lock() 
    msg = _("The lock could not be opened, sorry for the inconvenience.") if msg != True else ""
    return HttpResponse(msg)

