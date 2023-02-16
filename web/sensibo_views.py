from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate, set_session, reverse_cardkey
from padword.decorators import group_required
from .models import *


'''
    Devices
'''
def get_device_project_context(project):
    context = {}
    context["project"] = project
    context["temp_range"] = range(16, 26)
    return context 

def get_item(project, uid, name, room_obj=None):
    item = {'uid': uid, 'name': name}
    item["measurement"] = project.sensibo_get_measurement(uid)
    item["ac_state"] = project.sensibo_get_ac_state(uid)
    if room_obj != None:
        item["room_obj"] = room_obj
    return item

@group_required("admins")
def devices_by_project(request, project_id):
    try:
        project = get_or_none(Project, project_id)
        device_list = project.sensibo_device_list()
        for dev in device_list:
            obj, created = SensiboDevice.objects.get_or_create(project_uuid=project.uuid, uuid=dev["uid"])
            if obj.name != dev["name"]:
                obj.name = dev["name"]
                obj.save()
            dev["measurement"] = project.sensibo_get_measurement(dev["uid"])
            dev["ac_state"] = project.sensibo_get_ac_state(dev["uid"])
            dev["room_obj"] = obj

        context = get_device_project_context(project)
        context['device_list'] = device_list
        return render (request, "web/sensibo/devices.html", context)
        #return render (request, "web/sensibo/devices.html", {'project': project, 'device_list': project.sensibo_device_list()})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def device_switch(request):
    try:
        project = get_or_none(Project, request.GET["obj_id"])
        name = get_param(request.GET, "name")
        uid = get_param(request.GET, "uid")
        ac_state = project.sensibo_get_ac_state(uid)
        msg = project.sensibo_change_ac_state(uid, ac_state)
        #msg = project.sensibo_change_ac_state_param(uid, ac_state, "fanLevel", "low")

        context = get_device_project_context(project)
        context['item'] = get_item(project, uid, name)
        context['msg'] = msg
        return render (request, "web/sensibo/device-list-row.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def device_set_state(request):
    try:
        project = get_or_none(Project, request.GET["obj_id"])
        name = get_param(request.GET, "name")
        uid = get_param(request.GET, "uid")
        param = get_param(request.GET, "param")
        value = get_param(request.GET, "value")
        ac_state = project.sensibo_get_ac_state(uid)
        if param == "targetTemperature":
            value = int(value)
        msg = project.sensibo_change_ac_state_param(uid, ac_state, param, value)

        context = get_device_project_context(project)
        context['item'] = get_item(project, uid, name)
        context["msg"] = msg
        return render (request, "web/sensibo/device-list-row.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def device_save_room(request):
    try:
        project = get_or_none(Project, request.GET["obj_id"])
        name = get_param(request.GET, "name")
        uid = get_param(request.GET, "uid")
        value = get_param(request.GET, "value")

        sd = SensiboDevice.objects.filter(project_uuid=project.uuid, uuid=uid).first()
        if sd != None:
            sd.room = value
            sd.save()

        context = get_device_project_context(project)
        context['item'] = get_item(project, uid, name, sd)
        #context["item"] = item
        return render (request, "web/sensibo/device-list-row.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


'''
    Devices by project
'''
@group_required("projects")
def devices_by_project2(request):
    try:
        project = get_or_none(Project, request.project_id)
        device_list = project.sensibo_device_list()
        for dev in device_list:
            dev["measurement"] = project.sensibo_get_measurement(dev["uid"])
            dev["ac_state"] = project.sensibo_get_ac_state(dev["uid"])

        context = get_device_project_context(project)
        context["device_list"] = device_list
        return render (request, "web/sensibo-by-project/devices.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def device_switch_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        name = get_param(request.GET, "name")
        uid = get_param(request.GET, "uid")
        ac_state = project.sensibo_get_ac_state(uid)
        msg = project.sensibo_change_ac_state(uid, ac_state)
        #msg = project.sensibo_change_ac_state_param(uid, ac_state, "fanLevel", "low")

        context = get_device_project_context(project)
        context['item'] = get_item(project, uid, name)
        context["msg"] = msg
        return render (request, "web/sensibo-by-project/device-list-row.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def device_set_state_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        name = get_param(request.GET, "name")
        uid = get_param(request.GET, "uid")
        param = get_param(request.GET, "param")
        value = get_param(request.GET, "value")
        ac_state = project.sensibo_get_ac_state(uid)
        if param == "targetTemperature":
            value = int(value)
        msg = project.sensibo_change_ac_state_param(uid, ac_state, param, value)

        context = get_device_project_context(project)
        context['item'] = get_item(project, uid, name)
        context["msg"] = msg
        return render (request, "web/sensibo-by-project/device-list-row.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


