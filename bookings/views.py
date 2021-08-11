from django.apps import apps
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc, get_or_none, get_param, get_float
from web.models import Channel, Company, Project, Device

from .common_lib import clone_form_instance, get_form_instance, get_max_index, get_or_create_answer_instance, user_in_group, write_log
from .models import AnswerInstance, Field, Form, FormInstance, FormType, Question, Block

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
            uuid_list = [item.uuid for item in Channel.objects.filter(project=project)]
            items = Form.objects.filter(channel__in = uuid_list)
            context["project"] = project
        elif company is not None:
            uuid_list = [item.uuid for item in Channel.objects.filter(project__company=company)]
            items = Form.objects.filter(channel__in = uuid_list)
            context["company"] = company
        else:
            items = Form.objects.all()
        context["items"] = items
        context["form_type_list"] = FormType.objects.all()
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

        company_id = get_param(request.GET, "company_id")
        project_id = get_param(request.GET, "project_id")
        channel_id = get_param(request.GET, "channel_id")
        if channel_id != "":
            channel = get_or_none(Channel, channel_id)
            if channel != None:
                obj.channel = channel.uuid
                obj.save()

        context = {'obj': obj, 'channel_id': channel_id, 'project_id': project_id, 'company_id': company_id}
        context["form_type_list"] = FormType.objects.all()
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

'''
    Bookings
'''
@login_required
def bookings(request, form_id):
    try:
        form = get_or_none(Form, form_id)
        if form != None:
            items = FormInstance.objects.filter(form = form)
            return render (request, "bookings/bookings.html", {'items': items, 'form': form})
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@login_required
def booking_new(request, form_id):
    try:
        form = get_or_none(Form, form_id)
        if form != None:
            fi = FormInstance.objects.create(form = form)
            write_log(request.user, fi, _("Booking created"))
            return redirect(booking_edit, fi.id)
    except Exception as e:
        logger.error("[bookings-new_booking] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@login_required
def booking_edit(request, fi_id, rol=None):
    try:
        fi = FormInstance.objects.get(pk = fi_id)
        block = fi.form.blocks.first()
        context = {'fi': fi, 'b': block, 'index': "0",}
        return render(request, 'bookings/fillform.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-fill_form] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@login_required
def booking_remove(request, fi_id):
    try:
        fi = FormInstance.objects.get(pk = fi_id)
        context = {'msg': FormInstance.CANCELED}
        return render(request, 'bookings/show_msg.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-remove_fi] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@login_required
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

@login_required
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

@login_required
def status_form(request):
    try:
        obj = get_or_none(FormInstance, request.GET["obj_id"]) if "obj_id" in request.GET else FormInstance.objects.create()
        return render(request, "bookings/status-form.html", {'obj': obj,})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@login_required
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
        block = get_or_none(QuestionBlock, request.GET["obj_id"])
        if fi != None and block != None:
            context = { 'fi': fi, 'b': block, 'index': "0"}
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
            context = { 'fi': fi, 'q': q, 'index': (max_index + 1), }
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


