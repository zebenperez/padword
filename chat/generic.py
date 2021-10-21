#!/usr/bin/python
#-*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .utils import pop_element
# from django.contrib.auth.models import User

import logging
logger = logging.getLogger(__name__)

# ----------
# Utils
# ----------

def get_feedback_pk(feedback_dic):
    return feedback_dic.get('form_data', {}).get('pk', None)

def get_session_feedback(context, request):
    context['success'] = pop_element(request.session, "success")
    context['error'] = pop_element(request.session, "error")
    context['form_data'] = pop_element(request.session, 'form_data')
    return context

def save_instance(app, form_class_name, params, files_params):

    datas = {}
    instance, error, success = [None] * 3

    mod = __import__(app + ".forms")
    mod = getattr(mod, "forms")

    form_class = getattr(mod, form_class_name)
    form = form_class(params, files_params)

    # TODO este codigo es para permitir edición
    pk = params.get('pk', None)
    if pk:
        instance = form_class._meta.model.objects.get(pk=pk)
        form = form_class(params, files_params, instance=instance)
        datas = form.__dict__.get("data", {}).copy()
        if form.is_valid():
            instance = form.save()
            success = "El elemento se ha modificado correctamente"
            datas['pk'] = instance.pk
        else:
            instance = form.instance
            error = form.errors
    else:
        form = form_class(params, files_params)
        datas = form.__dict__.get("data", {}).copy()
        if form.is_valid():
            instance = form.save()
            # logger.info("saved")
            success = "El elemento se ha creado correctamente"
            datas['pk'] = instance.pk

        else:
            logger.error(form.errors)
            instance = form.instance
            error = form.errors

    return datas, instance, success, error

# ------------
# VIEWS
# -----------

def error404(request):

    context = {}
    return render(request, "error404.html", context)


@login_required
def form_save(request, app, form_class_name):
    errors = ""
    success = None
    instance = None
    datas = {}
    next_url = "/"
    if request.method == "POST":
        next_url = request.POST.get("next", None)
        try:
            datas, instance, success, error = save_instance(app, form_class_name, request.POST, request.FILES)
            errors = (errors + ",%s" % error) if error else errors
            if not error:
                inline_forms = request.POST.getlist("inline-forms", [])

                for item in inline_forms:
                    try:
                        if_app, if_form_class_name, if_fields = item.split("|")
                        if_fields = if_fields.split(",")
                        instances = int(request.POST.get("%s-forms-num" % if_form_class_name, "0"))
                        parent_fk = request.POST.get("%s-parent-fk" % if_form_class_name, "")
                        for i in range(1, instances + 1):
                            fields_dict = {parent_fk: instance.pk}
                            files_dict = {}
                            for name in if_fields:
                                key = "%s-%s-%s" % (if_form_class_name, name, i)
                                fields_dict[name] = request.POST.get(key, None)
                                files_dict[name] = request.FILES.get(key, None)

                            response = save_instance(if_app, if_form_class_name, fields_dict, files_dict)
                            if len(response) > 2:
                                if response[3]:
                                    errors += ", %s" % (response[3])

                    except Exception as e:
                        logger.error("generic-formsave-Err1" + str(e))
                        error = str(e)
        except Exception as e:
            logger.error("[generic-formsave-Err2]" + str(e))
            error = "Error de carga de módulo"
    else:
        error = "Ha habido un error al procesar el formulario"
        logger.error(error)

    request.session['success'] = success
    request.session['error'] = errors
    request.session['form_data'] = datas
    return redirect(next_url)
