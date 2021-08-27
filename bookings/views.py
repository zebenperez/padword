from django.apps import apps
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, get_bool, new_ui_slug
from web.models import Channel, Company, Project, Device
from contents.models import Category, ShoppingCart, Item
from guest.models import Guest

from .common_lib import clone_form_instance, get_form_instance, get_max_index, get_or_create_answer_instance, user_in_group, write_log
from .models import AnswerInstance, AnswerType, Field, Form, FormChannel, FormInstance, FormType, Question, QuestionType, Block

import datetime
import logging
logger = logging.getLogger(__name__)


'''
    Forms
'''
def get_edit_context(obj):
    return {
        'obj': obj,
        'block_list': Block.objects.all(),
        'form_type_list': FormType.objects.all(),
        'answer_type_list': AnswerType.objects.all(),
        'question_type_list': QuestionType.objects.all()
    }

@group_required("admins", "projects")
def forms(request):
    try:
        context = { 'items': Form.objects.all(), }
        return render (request, "forms/forms.html", {'items': Form.objects.all()})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
def forms_by_project(request, project_id):
    try:
        project = get_or_none(Project, project_id)
        if project != None:
            uuid_list = [item.uuid for item in Category.objects.filter(project_uuid=project.uuid)]
            context = { 'items': Form.objects.filter(category__in=uuid_list), }
            return render (request, "forms/forms.html", {'items': Form.objects.all()})
        else:
            return render(request, 'error_exception.html', {'msg': 'Project not found!'})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
def form_search(request):
    try:
        project = get_param(request.GET, "s-project")
        channel = get_param(request.GET, "s-channel")
        name = get_param(request.GET, "s-name")

        kwargs = {}
        if project != "":
            uuid_project_list = [item.uuid for item in Project.objects.filter(name__icontains=project)]
            uuid_list = [item.uuid for item in Category.objects.filter(project_uuid__in=uuid_project_list)]
            kwargs["category__in"] = uuid_list
        if channel != "":
            uuid_list = [item.uuid for item in Channel.objects.filter(name__icontains=channel)]
            kwargs["channels__channel__in"] = uuid_list
        if name != "":
            kwargs["name__icontains"] = name
        items = Form.objects.filter(**kwargs)

        return render(request, "forms/form-list.html", {'items':items,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def form_edit(request, form_id=None, category_uuid=None):
    try:
        # Edit instance
        if form_id != None:
            obj = get_or_none(Form, form_id)
            if obj == None:
                return render(request, 'error_exception.html', {'exc': _('Form not found!')})
        # Create or edit by category
        elif category_uuid != None:
            cat = get_or_none(Category, category_uuid, 'uuid')
            if cat == None:
                return render(request, 'error_exception.html', {'exc': _('Category not found!')})
            obj = get_or_none(Form, cat.uuid, 'category')
            if obj == None:
                obj = Form.objects.create(uuid=new_ui_slug(Form), category=cat.uuid)
        # New form
        else:
           obj = Form.objects.create(uuid=new_ui_slug(Form))

        context = get_edit_context(obj)
        return render(request, "forms/form-edit.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@login_required
def form_form(request):
    try:
        obj = get_or_none(Form, request.GET["obj_id"]) if "obj_id" in request.GET else None
        context = get_edit_context(obj)
        return render(request, "forms/form-edit-content.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@login_required
def form_remove(request, form_id=None):
    company_id = get_param(request.GET, "company_id", None)
    project_id = get_param(request.GET, "project_id", None)
    channel_id = get_param(request.GET, "channel_id", None)
    #obj = get_or_none(Form, request.GET["obj_id"]) if "obj_id" in request.GET else None
    obj = get_or_none(Form, form_id)
    if obj != None:
        obj.delete()
    context = get_forms(get_or_none(Channel, channel_id), get_or_none(Project, project_id), get_or_none(Company, company_id))
    return render (request, "forms/form-list.html", context)

@login_required
def form_add_image(request):
    try:
        obj_id = request.POST["obj_id"]
        image = request.FILES["file"]

        form = get_or_none(Form, obj_id)
        if form != None:
            form.image = image
            form.save()
        return render(request, "forms/form-document.html", {"obj": form,})
    except Exception as e:
        logger.error("[bookings-form_add_image]" + str(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

@login_required
def form_remove_image(request):
    try:
        obj_id = request.GET["obj_id"]
        obj = get_or_none(Form, obj_id) 
        obj.image.delete(save=False)
        return render(request, "forms/form-document.html", {"obj": obj,})
    except Exception as e:
        logger.error("[remove_file]" + str(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

@login_required
def channel_add(request):
    value = request.GET["value"] if "value" in request.GET else None
    obj = get_or_none(Form, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None and value != "":
        FormChannel.objects.create(channel=value, form=obj)
    return render (request, "forms/channel-form.html", {'obj': obj})

@login_required
def channel_remove(request):
    obj = get_or_none(FormChannel, request.GET["obj_id"]) if "obj_id" in request.GET else None
    form = None
    if obj != None:
        form = obj.form
        obj.delete()
    return render (request, "forms/channel-form.html", {'obj': form})

@login_required
def block_add(request):
    obj = get_or_none(Form, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        block = Block.objects.create(order=Block.get_max_order(obj), form=obj)
        Question.objects.create(block=block)
    context = {'obj': obj, 'answer_type_list': AnswerType.objects.all(), 'question_type_list': QuestionType.objects.all()}
    return render (request, "forms/block-form.html", context)

@login_required
def block_remove(request):
    obj = get_or_none(Block, request.GET["obj_id"]) if "obj_id" in request.GET else None
    form = None
    if obj != None:
        form = obj.form
        obj.delete()
    return render (request, "forms/block-form.html", {'obj': form})

@login_required
def field_add(request):
    obj = get_or_none(Question, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        Field.objects.create(order=Field.get_max_order(obj), question=obj)
    context = {'q': obj, 'answer_type_list': AnswerType.objects.all(), 'question_type_list': QuestionType.objects.all()}
    return render (request, "forms/question-form.html", context)

@login_required
def field_remove(request):
    obj = get_or_none(Field, request.GET["obj_id"]) if "obj_id" in request.GET else None
    question = None
    if obj != None:
        question = obj.question
        obj.delete()
    return render (request, "forms/question-form.html", {'q': question})

'''
    Bookings
'''
def get_booking_context(form=None, project=None):
    context = {}
    today = datetime.datetime.today()

    kwargs = {'date__year': today.year, 'date__month': today.month, 'date__day': today.day}
    if form != None:
        kwargs['form_uuid'] = form.uuid
        context["form_name"] = form.name
        if form.channels.all().count() == 1:
            fc = form.channels.first()
            channel = Channel.objects.filter(uuid = fc.channel).first()
            context["channel_name"] = channel.name
            context["project_name"] = channel.project.name
    if project != None:
        uuid_list = [item.uuid for item in Channel.objects.filter(project=project)]
        kwargs["form__channels__channel__in"] = uuid_list
        context["project_name"] = project.name

    items = FormInstance.objects.filter(**kwargs)

    context["ini_date"] = today
    context["end_date"] = today
    context["items"] = items
    return context

@group_required("admins")
def bookings(request):
    try:
        context = get_booking_context()
        return render (request, "bookings/bookings.html", context)
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def bookings_by_form(request, form_id):
    try:
        if hasattr(request, "project_id"):
            context = get_booking_context(form=get_or_none(Form, form_id), project=get_or_none(Project, request.session["project_id"]))
        else:
            context = get_booking_context(form=get_or_none(Form, form_id))
        return render (request, "bookings/bookings.html", context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-bookings_by_form] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def bookings_by_project(request, project_id):
    try:
        context = get_booking_context(project=get_or_none(Project, project_id))
        return render (request, "bookings/bookings.html", context)
    except Exception as e:
        logger.error("[bookings-bookings_by_project] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def bookings_search(request):
    try:
        project = get_param(request.GET, "s-project")
        channel = get_param(request.GET, "s-channel")
        form = get_param(request.GET, "s-form")
        ini_date = get_param(request.GET, "s-ini_date")
        end_date = get_param(request.GET, "s-end_date")
        name = get_param(request.GET, "s-name")
        status = get_param(request.GET, "s-status")

        kwargs = {}
        if project != "":
            uuid_list = [item.uuid for item in Channel.objects.filter(project__name__icontains=project)]
            kwargs["form__channels__channel__in"] = uuid_list
        if channel != "":
            uuid_list = [item.uuid for item in Channel.objects.filter(name__icontains=channel)]
            kwargs["form__channels__channel__in"] = uuid_list
        if form != "":
            kwargs["form__name__icontains"] = form
        if ini_date != "":
            kwargs["date__gte"] = ini_date
        if end_date != "":
            kwargs["date__lte"] = end_date
        if name != "":
            kwargs["name__icontains"] = name
        if status != "":
            kwargs["status"] = status
        items = FormInstance.objects.filter(**kwargs)

        return render(request, "bookings/booking-list.html", {'items':items,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
#def booking_edit(request, fi_id, ro=1):
def booking_view(request, fi_id):
    try:
        fi = FormInstance.objects.get(pk = fi_id)
        form = get_or_none(Form, fi.form_uuid, 'uuid')
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk)
        #context = {'fi': fi, 'index': "0", "ro": (ro == 1), 'items':items}
        context = {'fi': fi, 'index': "0", "ro": True, 'items':items}
        return render(request, 'bookings/fillform.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-fill_form] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def change_status(request):
    try:
        if request.POST:
            fi = FormInstance.objects.get(pk = request.POST["fi_id"])
            previous_status = fi.get_status_display()
            fi.status = request.POST["status"]
            fi.save()
            write_log(request.user, fi, _("Status change from {} to {}".format(previous_status, fi.get_status_display())))
            return redirect(bookings_by_form, fi.form.id)
    except Exception as e:
        print(e)
        logger.error("[bookings-change_status] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def status_form(request):
    try:
        obj = get_or_none(FormInstance, request.GET["obj_id"]) if "obj_id" in request.GET else FormInstance.objects.create()
        return render(request, "bookings/status-form.html", {'obj': obj,})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def booking_log(request, fi_id):
    try:
        fi = get_or_none(FormInstance, fi_id)
        return render(request, 'bookings/booking-logs.html', {'fi': fi})
    except Exception as e:
        logger.error("[bookings-new_booking] {}".format(str(e)))
    return render(request, 'error_exception.html', {})


'''
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

@login_required
def test(request):
    form_id = request.GET["form_id"]
    return HttpResponse(form_id)

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
        return render(request, "bookings/shopping-form.html", {'obj':obj})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

#@login_required
def show_category_shopping_cart(request):
    try:
        form_id = request.GET["form_id"]
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

#@login_required
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

'''
    Bookings client methods
'''
#@login_required
def booking_new(request, form_uuid, device_uuid=""):
    try:
        form = Form.objects.filter(uuid = form_uuid).first()
        if form != None:
            fi = FormInstance.objects.create(form_uuid = form.uuid, device_uuid = device_uuid)
            write_log(request.user, fi, _("Booking created"))
            #return redirect(booking_edit, fi.id, 0)
        
            items = ShoppingCart.objects.filter(form_instance_id=fi.pk)
            context = {'fi': fi, 'index': "0", "ro": False, 'items':items}
            return render(request, 'bookings/fillform.html', context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-new_booking] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})
    return render(request, 'error_exception.html', {'exc':'Form is None'})

#@group_required("admins", "projects", "clients")
def booking_send(request, fi_id):
    try:
        fi = FormInstance.objects.get(pk = fi_id)
        previous_status = fi.get_status_display()
        fi.status = "02"
        fi.save()
        write_log(request.user, fi, _("Status change from {} to {}".format(previous_status, fi.get_status_display())))
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
        context = {'msg': FormInstance.CANCELED, 'device_uuid': device_uuid}
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


