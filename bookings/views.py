from django.apps import apps
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from padword.commons import show_exc, get_or_none, get_param, get_float

from .common_lib import clone_form_instance, get_form_instance, get_max_index, get_or_create_answer_instance, user_in_group
from .models import AnswerInstance, Field, Form, FormInstance, Question, Block

import logging
logger = logging.getLogger(__name__)


'''
    Forms
'''
@login_required
def forms(request):
    try:
        items = Form.objects.all()
        return render(request, "forms/forms.html", {'items':items,})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def form_search(request):
    try:
        name = get_param(request.GET, "s-name")
        filters_to_search = ["name__icontains", "channel__icontains"]
        items = Form.objects.none()
        for myfilter in filters_to_search:
            kwargs = {}
            if name != "":
                kwargs[myfilter] = name
            items = items.union(Form.objects.filter(**kwargs))
        return render(request, "forms/form-list.html", {'items': items,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def form_form(request):
    try:
        obj = get_or_none(Form, request.GET["obj_id"]) if "obj_id" in request.GET else Form.objects.create()

        return render(request, "forms/form-form.html", {'obj': obj,})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@login_required
def form_remove(request):
    obj = get_or_none(Form, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()

    items = Form.objects.all()
    return render(request, "forms/form-list.html", {'items':items})


'''
    Form Instances
'''
@login_required
def fill_form(request, fi_id, rol=None):
    try:
        fi = FormInstance.objects.get(pk = fi_id)
        block = fi.form.blocks.first()
        context = {'fi': fi, 'b': block, 'index': "0",}
        return render(request, 'bookings/fillform.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-fill_form] {}".format(str(e)))
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


