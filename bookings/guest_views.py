from django.apps import apps
from django.contrib import auth
#from django.db.models import Q
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 
from django.views.i18n import check_for_language

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, get_bool, new_ui_slug
from web.models import Device, Project, ProjectUser
from contents.models import Category, ShoppingCart, Item
from guest.models import Guest

from .common_lib import get_or_create_form_instance, get_max_index, get_or_create_answer_instance, user_in_group
from .models import AnswerInstance, Field, Form, FormChannel, FormInstance, Question, Block, GuestUser, Status
from django.conf import settings


import datetime
import logging
logger = logging.getLogger(__name__)

'''
    Bookings client methods
'''
def check_user(user, form_uuid="", project_uuid=""):
    if not user.is_authenticated:
        return False
    if not user_in_group(user, "guests"):
        return False
    if form_uuid != "":
        form = get_or_none(Form, form_uuid, "uuid")
        if form == None or form.project == None:
            return False
        project_uuid = form.project.uuid
    if project_uuid == "":
        return False

    guest = Guest.check_valid_booking(project_uuid, user.username)
    if guest == None:
        return False

    return True

#def guest_access(request, form_uuid):
#    device_imei = request.GET["device_imei"] if "device_imei" in request.GET else ""
#    room_number = request.GET["room_number"] if "room_number" in request.GET else ""
#    guest_name = request.GET["guest_name"] if "guest_name" in request.GET else ""
#    guest_surname = request.GET["guest_surname"] if "guest_surname" in request.GET else ""
#
#    if check_user(request.user, form_uuid=form_uuid):
#        next_url = "booking-new"
#    else:
#        auth.logout(request)
#        next_url="booking-new-device" if device_imei != "" and room_number != "" and guest_name != "" and guest_surname != "" else "guest-form-login"
#
#    context = {
#        'form_uuid': form_uuid,
#        'device_imei': device_imei,
#        'room_number': room_number,
#        'guest_name': guest_name,
#        'guest_surname': guest_surname,
#        'next_url': next_url
#    }
#    return render(request, 'bookings/guest/guest-welcome.html', context)
#
#def guest_access_bookings(request, project_uuid):
#    if check_user(request.user, project_uuid=project_uuid):
#        next_url = reverse("my-bookings")
#    else:
#        auth.logout(request)
#        next_url = reverse("guest-form-login")
#    context = {'project_uuid': project_uuid, 'next_url': next_url}
#    return render(request, 'bookings/guest/guest-welcome.html', context)
#
#def guest_access_pwa(request, project_uuid):
#    if check_user(request.user, project_uuid=project.uuid):
#        next_url = reverse("pwa-index-cat")
#    else:
#        auth.logout(request)
#        next_url = reverse("guest-form-login")
#    context = {'project_uuid': project_uuid, 'next_url': next_url}
#    return render(request, 'bookings/guest/guest-welcome.html', context)
#
#def guest_access_pwa(request, category_uuid, lang=None):
def guest_access(request, category_uuid, lang=None):
    cat = get_or_none(Category, category_uuid, "uuid")
    context = {'project_uuid': cat.project.uuid, 'cat': cat}
    if check_user(request.user, project_uuid=cat.project.uuid):
        next_url = reverse("pwa-index-cat", kwargs = {'category_uuid':category_uuid})
        guest = Guest.check_valid_booking(cat.project.uuid, request.user.username)
        context["guest"] = guest
    else:
        auth.logout(request)
        next_url = reverse("guest-form-login")
    context["next_url"] = next_url
    if lang:
        context["lang"] = lang
    #context = {'cat': cat}
    #return render(request, 'bookings/guest/guest-welcome-pwa.html', context)
    return render(request, 'bookings/guest/guest-welcome.html', context)


#def guest_form_login(request, form_uuid=None):
def guest_form_login(request):
    try:
        #if "form_uuid" in request.GET or form_uuid != None:
        #    form_uuid = request.GET["form_uuid"] if "form_uuid" in request.GET else form_uuid
        #    return render(request, 'guest_form_login.html', {'form_uuid': form_uuid})
        if "project_uuid" in request.GET:
            cat_uuid = request.GET["category_uuid"] if "category_uuid" in request.GET else ""
            return render(request, 'guest_form_login.html', {'project_uuid': request.GET["project_uuid"], 'category_uuid': cat_uuid})
        return render(request, 'error_exception.html', {'exc': 'Form or project not found!', 'error-msg': 'Form or project not found!'})
    except Exception as e:
        logger.error("[bookings-guest_form_login] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

def booking_new_guest(request):
    '''
        Guest access by form
    '''
    try:
        #date = datetime.datetime.now()
        #form_uuid = request.POST["form_uuid"]
        project_uuid = request.POST["project_uuid"]
        category_uuid = request.POST["category_uuid"]
        code = request.POST["code"]
        room = request.POST["room"]
        #guest = Guest.objects.filter(Q(mobile=code) | Q(email=code)).filter(room=room, check_in__lte=date, check_out__gte=date).first()
        #print (form_uuid, project_uuid)

        #if form_uuid != "":
        #    form = get_or_none(Form, form_uuid, "uuid")
        #    if form == None:
        #        return render(request, 'error_exception.html', {'exc': _('Form not found!')})
        #    if form.project == None:
        #        return render(request, 'error_exception.html', {'exc': _('Project not found!')})
        #    projects = [form.project]
        #else:
        project = get_or_none(Project, project_uuid, "uuid")
        if project == None:
            guests = Guest.objects.filter(email = code)
            projects = [guest.project for guest in guests]
        else:
            projects = [project]

                #return render(request, 'error_exception.html', {'exc': _('Project not found!')})

        guest = None
        for project in projects:
            guest = Guest.check_valid_booking(project.uuid, code, room)
            if guest != None:
                break

        if guest == None:
            #if form_uuid != "":
            #    return render(request, 'guest_form_login.html', {'form_uuid': form_uuid, 'error_msg':_('Sorry, your information is not right. Please, try again.')})
                #return render(request, "guest-error-login.html",  {'form_uuid':form_uuid})
            #if project_uuid != "":
            #    return redirect(reverse('guest-access-bookings', kwargs = {'project_uuid':project_uuid}))
            return render(request, 'error_exception.html', {'exc': 'Guest not found!'})

        user, err = GuestUser.get_or_create_guest_user(guest.UUID, project.uuid, code)
        if err != "":
            return render(request, 'error_exception.html', {'exc': err})
        auth.login(request, user)

        #return redirect(booking_new, form_uuid) if form_uuid != "" else redirect(bookings_by_guest, project.uuid)
        #return redirect(booking_new, form_uuid) if form_uuid != "" else redirect(reverse("pwa-index-cat", kwargs = {'category_uuid':category_uuid}))
        return redirect(reverse("pwa-index-cat", kwargs = {'category_uuid':category_uuid}))
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-new_booking] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

#def booking_new_device(request, form_uuid):
#def booking_new_device(request):
#    '''
#        Guest access by device
#    '''
#    try:
#        form_uuid = request.GET["form_uuid"] if "form_uuid" in request.GET else ""
#        device_imei = request.GET["device_imei"] if "device_imei" in request.GET else ""
#        room_number = request.GET["room_number"] if "room_number" in request.GET else ""
#        guest_name = request.GET["guest_name"] if "guest_name" in request.GET else ""
#        guest_surname = request.GET["guest_surname"] if "guest_surname" in request.GET else ""
#
#        if device_imei == "":
#            return redirect(guest_form_login, form_uuid)
#        device = get_or_none(Device, device_imei, "imei")
#        if device == None:
#            return redirect(guest_form_login, form_uuid)
#        if device.room != room_number:
#            return redirect(guest_form_login, form_uuid)
#        guest = Guest.objects.filter(name=guest_name, surname=guest_surname, room=room_number).first()
#        if guest == None:
#            return redirect(guest_form_login, form_uuid)
#        code = guest.get_code()
#        if code == "":
#            return render(request, 'error_exception.html', {'exc': _('Guest not found or not assigned to room number!')})
#        form = get_or_none(Form, form_uuid, "uuid")
#        if form == None:
#            return render(request, 'error_exception.html', {'exc': _('Form not found!')})
#        if form.project == None:
#            return render(request, 'error_exception.html', {'exc': _('Project not found!')})
#
#        user, err = GuestUser.get_or_create_guest_user(guest.UUID, form.project.uuid, code)
#        if err != "":
#            return render(request, 'error_exception.html', {'exc': err})
#        auth.login(request, user)
#
#        return redirect(booking_new, form_uuid)
#    except Exception as e:
#        print (show_exc(e))
#        logger.error("[bookings-new_booking] {}".format(str(e)))
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})
# 
#@group_required("admins", "projects", "guests")
#def booking_new(request, form_uuid):
#    '''
#        Guest access by form
#    '''
#    try:
#        form = get_or_none(Form, form_uuid, "uuid")
#        if form == None:
#            return render(request, 'error_exception.html', {'exc': _('Form not found!')})
#        if form.project == None:
#            return render(request, 'error_exception.html', {'exc': _('Project not found!')})
#
#        gu = GuestUser.objects.filter(project_uuid=form.project.uuid, username=request.user.username).first()
#        if gu == None or gu.guest == None:
#            return render(request, 'error_exception.html', {'exc': 'User not found!'})
#
#        fi = get_or_create_form_instance(form, gu.guest.UUID)
#        #write_log(request.user, fi, _("Booking created"))
#        
#        items = ShoppingCart.objects.filter(form_instance_id=fi.pk) if fi != None else []
#        context = {'fi': fi, 'form': form, 'index': "0", "ro": False, 'items':items}
#        return render(request, 'bookings/show-category.html', context)
#    except Exception as e:
#        print (show_exc(e))
#        logger.error("[bookings-new_booking] {}".format(str(e)))
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})
#
@group_required("admins", "projects", "guests")
#def booking_send(request, fi_id):
def booking_send(request):
    try:
        fi_id = request.GET["obj_id"]
        fi = FormInstance.objects.get(pk = fi_id)
        fi.set_status("01", request.user, "")
        fi.date = datetime.datetime.now()
        fi.save()
        context = {'msg': fi.get_status.status.code}
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
        #project_uuid = fi.form.project.uuid if fi.form != None and fi.form.project != None else ""
        #cat_uuid = fi.form.category if fi.form != None else ""
        fi.delete()
        #context = {'msg': "05", 'project_uuid': project_uuid}
        context = {'msg': "05"}
        return render(request, 'bookings/guest/show-msg.html', context)
    except Exception as e:
        logger.error("[bookings-remove_fi] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

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
        cat_uuid = request.GET["cat_id"] if "cat_id" in request.GET else ""
        context = {
            'items': FormInstance.objects.filter(guest_uuid=guest.UUID, date__range=[guest.check_in, guest.check_out], status_list__isnull=False).distinct(),
            'status_list': Status.objects.all(),
            'cat_uuid': cat_uuid,
            'guest': guest
        }
        print(context["items"])
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
        cat_uuid = request.GET["cat_id"] if "cat_id" in request.GET else ""
        context = {'fi': fi, 'index': "0", 'project_uuid': form.project.uuid, 'items':items, 'cat_uuid': cat_uuid}
        return render(request, 'bookings/guest/view-booking.html', context)
        #template = 'bookings/guest/view-booking-project.html' if fi.form.form_type.code == "ecom" else 'bookings/guest/view-booking.html'
        #return render(request, template, context)
    except Exception as e:
        print(e)
        logger.error("[bookings-fill_form] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

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
        items = ShoppingCart.objects.filter(form_instance_id=int(form_id), item=item)

        total_price = "{:.2f}".format(instance.get_total)
        total_items = ShoppingCart.objects.filter(form_instance_id=int(form_id)).count()

        return render(request, "bookings/ecom/show-instance-result.html", {'items':items,'item':item,'total_price':total_price,'total_items':total_items})
        #return HttpResponse('{} art.&nbsp;&nbsp;&nbsp;{:.2f} &euro;'.format(items.count(), instance.get_total))
        #return render(request, "bookings/shopping-form.html", {'obj':obj})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
def show_category_shopping_cart(request, form_id=None, cat_id = None):
    try:
        if not form_id:
            form_id = request.GET["form_id"] if "form_id" in request.GET else 0
        if not cat_id:
            cat_id = request.GET["cat_id"] if "cat_id" in request.GET else ""
        #instance = FormInstance.objects.get(pk=form_id) if form_id != 0 else None
        instance = get_or_none(FormInstance, form_id)
        category = Category.objects.get(uuid=cat_id)
        form = Form.objects.filter(category=category.uuid).first()
        #form = ""
        #if instance != None:
        #    form = instance.form
        #elif category != None:
        #    form = Form.objects.filter(category=category.uuid).first()
        #return render(request, "bookings/ecom/shopping_cart.html", {'category':category, 'fi':instance})
        return render(request, form.form_type.template, {'category':category, 'fi':instance})
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
        instance_id = get_param(request.GET, "form_id")
        print("--1--")
        if instance_id != "":
            print("--1.1--")
            instance = FormInstance.objects.get(pk=instance_id)
            items = ShoppingCart.objects.filter(form_instance_id=instance.pk)
            total_price = instance.get_total
            return render(request, "bookings/ecom/view-shopping-cart.html", {'fi':instance, 'items':items, 'total':total_price})
        else:
            print("--1.2--")
            gu = GuestUser.objects.filter(username=request.user.username).first()
            fi_list = FormInstance.objects.filter(guest_uuid = gu.guest.UUID, status_list__isnull=True)
            print(fi_list)
            items = ShoppingCart.objects.none()
            total_price = 0
            for instance in fi_list:
                items = ShoppingCart.objects.filter(form_instance_id=instance.pk) or items
                total_price += instance.get_total
            return render(request, "bookings/ecom/view-shopping-cart.html", {'fi':instance, 'items':items, 'total':total_price})
        return render(request, "bookings/ecom/view-shopping-cart.html", {'fi':None, 'items':[], 'total':0})
    except Exception as e:
        #return HttpResponse(show_exc(e))
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
        instance_id = obj.form_instance_id
        item = obj.item
        obj.delete()
        instance = FormInstance.objects.get(pk=instance_id)
        items = ShoppingCart.objects.filter(form_instance_id=instance.pk)
        total_price = instance.get_total
        total_items = instance.items_in_bookings(item).count()
        return render(request, "bookings/ecom/view-shopping-cart.html", {'fi':instance, 'items':items, 'total':total_price, 'item_refresh':item, 'total_items':total_items})
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

        return render(request, "bookings/ecom/show-instance-result.html", {'items':items,'item':item,'total_price':total_price,'total_items':total_items})
        #return render(request, "bookings/show-instance-result.html", {'items':items, 'item':item})
        #return render(request, "bookings/view-shopping-cart.html", {'fi':instance, 'items':items, 'total':total_price})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

'''
    Bookings menu
'''
@group_required("admins", "projects", "guests")
#def show_category_menu(request, form_id=None, cat_id = None):
def show_category_menu(request, cat_id=None, lang=None):
    try:
        #if not form_id:
        #    form_id = request.GET["form_id"] if "form_id" in request.GET else 0
        if not cat_id:
            cat_id = request.GET["cat_id"] if "cat_id" in request.GET else 0
        category = get_or_none(Category, cat_id, "uuid")
        #instance = get_or_none(FormInstance, form_id)
        #form = ""
        #if instance != None:
        #    form = instance.form
        #elif category != None:
        #    form = Form.objects.filter(category=category.uuid).first()
        #return render(request, "bookings/menu.html", {'category':category, 'fi':instance})

        form = Form.objects.filter(category=category.uuid).first()
        gu = GuestUser.objects.filter(project_uuid=form.project.uuid, username=request.user.username).first()
        fi = get_or_create_form_instance(form, gu.guest.UUID) if gu != None and gu.guest != None else None
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk) if fi != None else []
        if len(items) == 0:
            ## FIXME! We have to filter by status
            fi_list = FormInstance.objects.filter(guest_uuid = gu.guest.UUID, status_list__isnull = True).values_list('pk', flat=True)
            items = ShoppingCart.objects.filter(form_instance_id__in = list(fi_list))

        response = render(request, form.form_type.template, {'category':category, 'form': form, 'fi':fi, 'index':0, 'items': items, 'guest':gu.guest, 'lang':lang})
        if lang and check_for_language(lang):
            if hasattr(request, 'session'):
                request.session['django_language'] = lang
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
 
        return  response
    except Exception as e:
        print(show_exc(e))
        return render(request, "error_exception.html", {'exc':show_exc(e)})

'''
    Bookings items
'''
@group_required("admins", "projects", "guests")
def show_item(request):
    try:
        item_id = request.GET["item_id"]
        item = get_or_none(Item, int(item_id))

        return render(request, "bookings/show-item-details.html", {'item':item,})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})


def close(request):
    return render(request, "close-window.html")

@group_required("admins", "projects", "guests")
def close_window(request):
    auth.logout(request)
    cat_uuid = request.GET["category_uuid"] if "category_uuid" in request.GET else ""
    return redirect(guest_access, cat_uuid)

#    project_uuid = request.GET["project_uuid"] if "project_uuid" in request.GET else ""
#    cat_uuid = request.GET["category_uuid"] if "category_uuid" in request.GET else ""
#    if cat_uuid == "" or project_uuid == "":
#        return render(request, 'error_exception.html', {'exc': 'Form or project not found!', 'error-msg': 'Form or project not found!'})
#    return render(request, 'guest_form_login.html', {'project_uuid': project_uuid, 'category_uuid': cat_uuid})
    #return render(request, "bookings/guest/close.html")

@group_required("admins", "projects", "guests")
def guest_notifications(request, form_id):
    try:
        #project_list = list(ProjectUser.objects.filter(username=request.user.username).values_list('project_uuid', flat=True))
        #categories_list = list(Category.objects.filter(project_uuid__in = projects_list).values_list('uuid', flat=True))
        #forms_list = list(Form.objects.filter(category__in = categories_list).values_list('uuid', flat=True))
        #bookings = FormInstance.objects.filter(form_uuid__in = forms_list, status__code = "01" ).order_by('pk')
        #return HttpResponse(str(bookings.count()))
        form = get_or_none(Form, form_id)
        gu = GuestUser.objects.filter(project_uuid=form.project.uuid, username=request.user.username).first()
        bookings = FormInstance.objects.filter(guest_uuid=gu.guest_uuid, status_list__read=False).order_by('pk')
        val = ""
        if len(bookings) > 0:
            val = _("You have some news in your orders:\n")
            for booking in bookings:
                val += _("Order {} with current status {}".format(booking.form.get_category.name, booking.get_status.status.name))
        return HttpResponse(val)
    except Exception as e:
        logger.error("[bookings-new_booking] {}".format(str(e)))
        print(e)
        return HttpResponse("")

@group_required("admins", "projects", "guests")
def set_guest_language(request, category_uuid, lang):
    try:
        #print(category_uuid)
        category = get_or_none(Category, category_uuid, "uuid")
        gu = GuestUser.objects.filter(project_uuid=category.project_uuid, username=request.user.username).first()
        guest = Guest.objects.get(pk=gu.guest.pk)
        guest.language = lang
        guest.save()
        if lang and check_for_language(lang):
            if hasattr(request, 'session'):
                request.session['django_language'] = lang
#             else:
#                 response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
        return redirect(reverse('show-category-menu', kwargs={'cat_id':category.uuid, 'lang':lang}))
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc': show_exc(e), 'error-msg': show_exc(e)})

@group_required("admins", "projects", "guests")
def reload_top_menu(request, category_uuid):
    try:
        category = get_or_none(Category, category_uuid, "uuid")
        return render(request, "bookings/top-menu.html", {'category':category})
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc': show_exc(e), 'error-msg': show_exc(e)})
