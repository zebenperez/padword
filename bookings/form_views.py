from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, get_bool, new_ui_slug
from web.models import Channel, Company, Device, Project, ProjectUser
from contents.models import Category

from .common_lib import generate_qr
from .models import AnswerType, Field, Form, FormChannel, FormInstance, FormType, Question, QuestionType, Block, Status

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
        return render(request, 'full_error_exception.html', {'exc':show_exc(e)})

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
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

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
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
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

@group_required("admins", "projects")
def form_form(request):
    try:
        obj = get_or_none(Form, request.GET["obj_id"]) if "obj_id" in request.GET else None
        context = get_edit_context(obj)
        return render(request, "forms/form-edit-content.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
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

@group_required("admins", "projects")
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

@group_required("admins", "projects")
def form_remove_image(request):
    try:
        obj_id = request.GET["obj_id"]
        obj = get_or_none(Form, obj_id) 
        obj.image.delete(save=True)
        return render(request, "forms/form-document.html", {"obj": obj,})
    except Exception as e:
        logger.error("[remove_file]" + str(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects")
def form_add_qr(request):
    try:
        obj_id = request.GET["obj_id"]
        form = get_or_none(Form, obj_id)
        if form != None:
            url = request.build_absolute_uri(reverse('guest-form-login', kwargs={'form_uuid': form.uuid}))
            img_data = ContentFile(generate_qr(url))
            form.qr.save('qr_{}.png'.format(form.uuid), img_data, save=True)
        return render(request, "forms/form-qr.html", {"obj": form,})
    except Exception as e:
        logger.error("[bookings-form_add_qr]" + str(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects")
def form_remove_qr(request):
    try:
        obj_id = request.GET["obj_id"]
        obj = get_or_none(Form, obj_id) 
        obj.qr.delete(save=True)
        return render(request, "forms/form-qr.html", {"obj": obj,})
    except Exception as e:
        logger.error("[remove_qr]" + str(e))
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects")
def channel_add(request):
    value = request.GET["value"] if "value" in request.GET else None
    obj = get_or_none(Form, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None and value != "":
        FormChannel.objects.create(channel=value, form=obj)
    return render (request, "forms/channel-form.html", {'obj': obj})

@group_required("admins", "projects")
def channel_remove(request):
    obj = get_or_none(FormChannel, request.GET["obj_id"]) if "obj_id" in request.GET else None
    form = None
    if obj != None:
        form = obj.form
        obj.delete()
    return render (request, "forms/channel-form.html", {'obj': form})

@group_required("admins", "projects")
def block_add(request):
    obj = get_or_none(Form, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        block = Block.objects.create(order=Block.get_max_order(obj), form=obj)
        Question.objects.create(block=block)
    context = {'obj': obj, 'answer_type_list': AnswerType.objects.all(), 'question_type_list': QuestionType.objects.all()}
    return render (request, "forms/block-form.html", context)

@group_required("admins", "projects")
def block_remove(request):
    obj = get_or_none(Block, request.GET["obj_id"]) if "obj_id" in request.GET else None
    form = None
    if obj != None:
        form = obj.form
        obj.delete()
    return render (request, "forms/block-form.html", {'obj': form})

@group_required("admins", "projects")
def field_add(request):
    obj = get_or_none(Question, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        Field.objects.create(order=Field.get_max_order(obj), question=obj)
    context = {'q': obj, 'answer_type_list': AnswerType.objects.all(), 'question_type_list': QuestionType.objects.all()}
    return render (request, "forms/question-form.html", context)

@group_required("admins", "projects")
def field_remove(request):
    obj = get_or_none(Field, request.GET["obj_id"]) if "obj_id" in request.GET else None
    question = None
    if obj != None:
        question = obj.question
        obj.delete()
    return render (request, "forms/question-form.html", {'q': question})

