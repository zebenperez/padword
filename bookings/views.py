from django.apps import apps
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, get_bool
from web.models import Channel, Company, Project, Device
from contents.models import Category

from .common_lib import clone_form_instance, get_form_instance, get_max_index, get_or_create_answer_instance, user_in_group, write_log
#from .models import AnswerInstance, Field, Form, FormChannel, FormInstance, FormType, Question, Block
from .models import AnswerInstance, Field, Form, FormChannel, FormInstance, Question, Block

import datetime
import logging
logger = logging.getLogger(__name__)


'''
    Forms
'''
def get_forms(channel, project, company):
    try:
        context = {}
        if channel is not None:
            items = Form.objects.filter(channel = channel.uuid)
            context["channel"] = channel
        elif project is not None:
            uuid_list = [item.uuid for item in Category.objects.filter(project_uuid=project.uuid)]

            items = Form.objects.filter(category__in = uuid_list)
            #items = Form.objects.filter(channels__in = uuid_list)
            context["project"] = project
        elif company is not None:
            uuid_list = [item.uuid for item in Channel.objects.filter(project__company=company)]
            items = Form.objects.filter(channels__in = uuid_list)
            context["company"] = company
        else:
            items = Form.objects.all()
        context["items"] = items
        #context["form_type_list"] = FormType.objects.all()
        context["block_list"] = Block.objects.all()
        return context
    except Exception as e:
        print(show_exc(e))
        return {'items':Form.objects.none()}


@login_required
def forms(request, project_id=None, company_id=None, channel_id=None):
    try:
        context = get_forms(get_or_none(Channel, channel_id), get_or_none(Project, project_id), get_or_none(Company, company_id))
        return render (request, "forms/forms.html", context)
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def form_search(request):
    try:
        company_id = get_param(request.GET, "company_id")
        project_id = get_param(request.GET, "project_id")
        channel_id = get_param(request.GET, "channel_id")
        company = get_or_none(Company, company_id)
        project = get_or_none(Project, project_id)
        channel = get_or_none(Channel, channel_id)
        name = get_param(request.GET, "s-name")
        filters_to_search = ["name__icontains", "channel__icontains"]
        items = Form.objects.none()
        for myfilter in filters_to_search:
            kwargs = {}
            if company != None:
                uuid_list = [item.uuid for item in Channel.objects.filter(project__company=company)]
                kwargs["channel__in"] = uuid_list
            if project != None:
                uuid_list = [item.uuid for item in Channel.objects.filter(project=project)]
                kwargs["channel__in"] = uuid_list
            if channel != None:
                kwargs["channel"] = channel.uuid
            if name != "":
                kwargs[myfilter] = name
            items = items.union(Form.objects.filter(**kwargs))
        return render(request, "forms/form-list.html", {'items':items,'channel_id':channel_id,'project_id':project_id,'company_id':company_id,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def form_form(request):
    try:
        obj = get_or_none(Form, request.GET["obj_id"]) if "obj_id" in request.GET else Form.objects.create()
        cat = get_or_none(Category, request.GET["category_id"], 'uuid') if "category_id" in request.GET else None
        if cat is None:
            company_id = get_param(request.GET, "company_id")
            project_id = get_param(request.GET, "project_id")
        else:
            company_id = cat.company.pk
            project_id = cat.project.pk
            
        channel_id = get_param(request.GET, "channel_id")
        if channel_id != "":
            channel = get_or_none(Channel, channel_id)
            if channel != None:
                obj.channel = channel.uuid
                obj.save()
        if cat != None:
            obj.category = cat.uuid
            obj.save()

        context = {'obj': obj, 'channel_id': channel_id, 'project_id': project_id, 'company_id': company_id}
        #context["form_type_list"] = FormType.objects.all()
        context["block_list"] = Block.objects.all()
        return render(request, "forms/form-form.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@login_required
def form_remove(request):
    company_id = get_param(request.GET, "company_id", None)
    project_id = get_param(request.GET, "project_id", None)
    channel_id = get_param(request.GET, "channel_id", None)
    obj = get_or_none(Form, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    context = get_forms(get_or_none(Channel, channel_id), get_or_none(Project, project_id), get_or_none(Company, company_id))
    return render (request, "forms/form-list.html", context)

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


'''
    Bookings
'''
#def get_bookings(form, channel, project):
#    try:
#        context = {}
#        if form is not None:
#            items = FormInstance.objects.filter(form = form)
#            context["form"] = form
#        elif channel is not None:
#            items = FormInstance.objects.filter(form__channel = channel.uuid)
#            context["channel"] = channel
#        elif project is not None:
#            uuid_list = [item.uuid for item in Channel.objects.filter(project=project)]
#            items = FormInstance.objects.filter(form__channel__in = uuid_list)
#            context["project"] = project
#        else:
#            items = FormInstance.objects.all()
#        context["items"] = items
#        context["form_list"] = Form.objects.all()
#        return context
#    except Exception as e:
#        print(show_exc(e))
#        return {'items':FormInstance.objects.none()}
#
#
#@login_required
#def bookings(request, form_id=None, project_id=None, channel_id=None):
#    try:
#        context = get_bookings(get_or_none(Form, form_id), get_or_none(Channel, channel_id), get_or_none(Project, project_id))
#        return render (request, "bookings/bookings.html", context)
#    except Exception as e:
#        logger.error("[bookings-bookings] {}".format(str(e)))
#    return render(request, 'error_exception.html', {})
#
#@login_required
#def bookings_search(request):
#    try:
#        project_id = get_param(request.GET, "s-project")
#        channel_id = get_param(request.GET, "s-channel")
#        project = get_or_none(Project, project_id)
#        channel = get_or_none(Channel, channel_id)
#        name = get_param(request.GET, "s-name")
#        form_id = get_param(request.GET, "s-form")
#        #filters_to_search = ["name__icontains", "channel__icontains"]
#        #items = Form.objects.none()
#        #for myfilter in filters_to_search:
#
#        kwargs = {}
#        if project != None:
#            uuid_list = [item.uuid for item in Channel.objects.filter(project=project)]
#            kwargs["channel__in"] = uuid_list
#        if channel != None:
#            kwargs["channel"] = channel.uuid
#        if name != "":
#            #kwargs[myfilter] = name
#            kwargs["name__icontains"] = name
#        if form_id != "":
#            kwargs["form__id"] = form_id
#        items = FormInstance.objects.filter(**kwargs)
#
#            #items = items.union(Form.objects.filter(**kwargs))
#
#        return render(request, "bookings/booking-list.html", {'items':items,'channel_id':channel_id,'project_id':project_id,'form_id':form_id,})
#    except Exception as e:
#        print (show_exc(e))
#        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})
#

def get_booking_context(form=None, project=None):
    context = {}
    today = datetime.datetime.today()

    kwargs = {'date__year': today.year, 'date__month': today.month, 'date__day': today.day}
    if form != None:
        kwargs['form'] = form
        context["form_name"] = form.name
    if project != None:
        uuid_list = [item.uuid for item in Channel.objects.filter(project=project)]
        kwargs["form__channels__channel__in"] = uuid_list
        context["project_uuid"] = project.uuid

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

        kwargs = {}
        if project != "":
            uuid_list = [item.uuid for item in Channel.objects.filter(project__uuid=project)]
            kwargs["form__channels__channel__in"] = uuid_list
        if channel != "":
            kwargs["form__channels__channel__in"] = channel
        if form != "":
            kwargs["form__name__icontains"] = form
        if ini_date != "":
            kwargs["date__gte"] = ini_date
        if end_date != "":
            kwargs["date__lte"] = end_date
        if name != "":
            kwargs["name__icontains"] = name
        items = FormInstance.objects.filter(**kwargs)

        return render(request, "bookings/booking-list.html", {'items':items,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})


@login_required
def booking_new(request, form_id, device_id=""):
    try:
        form = get_or_none(Form, form_id)
        if form != None:
            fi = FormInstance.objects.create(form = form, device = device_id)
            write_log(request.user, fi, _("Booking created"))
            return redirect(booking_edit, fi.id, 1)
    except Exception as e:
        logger.error("[bookings-new_booking] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def booking_edit(request, fi_id, ro=0):
    try:
        fi = FormInstance.objects.get(pk = fi_id)
        block = fi.form.blocks.first()
        context = {'fi': fi, 'b': block, 'index': "0", "ro": (ro == 1)}
        return render(request, 'bookings/fillform.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-fill_form] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins")
def booking_remove(request, fi_id):
    try:
        fi = FormInstance.objects.get(pk = fi_id)
        fi.delete()
        context = {'msg': FormInstance.CANCELED}
        return render(request, 'bookings/show_msg.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-remove_fi] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def set_status(request, fi_id, status):
    try:
        fi = FormInstance.objects.get(pk = fi_id)
        previous_status = fi.get_status_display()
        fi.status = status
        fi.save()
        write_log(request.user, fi, _("Status change from {} to {}".format(previous_status, fi.get_status_display())))
        context = {'msg': status}
        return render(request, 'bookings/show_msg.html', context)
    except Exception as e:
        logger.error("[bookings-change_status] {}".format(str(e)))
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
            return redirect(bookings, fi.form.id)
    except Exception as e:
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
    Remote
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


