from django.shortcuts import render, redirect
from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, get_bool, new_ui_slug
from contents.models import Category
from web.models import Project


'''
    Sensibo device options
'''
def get_item(project, uid, name):
    item = {'name': name, 'uid': uid}
    item["measurement"] = project.sensibo_get_measurement(uid)
    item["ac_state"] = project.sensibo_get_ac_state(uid)
    return item


@group_required("guests")
def show_sensibo_menu(request):
    try:
        cat_id = request.GET["cat_id"] if "cat_id" in request.GET else 0
        category = get_or_none(Category, cat_id, "uuid")
        project = category.project

        device_list = project.sensibo_device_list()
        for dev in device_list:
            dev["measurement"] = project.sensibo_get_measurement(dev["uid"])
            dev["ac_state"] = project.sensibo_get_ac_state(dev["uid"])

        context = {'category':category, 'project':project, 'temp_range':range(16, 26), 'device_list':device_list}
        return render(request, 'bookings/sensibo/devices.html', context)
    except Exception as e:
        print(show_exc(e))
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("guests")
def device_switch(request):
    try:
        project = get_or_none(Project, request.GET["obj_id"])
        name = get_param(request.GET, "name")
        uid = get_param(request.GET, "uid")
        ac_state = project.sensibo_get_ac_state(uid)
        msg = project.sensibo_change_ac_state(uid, ac_state)

        context = {'project':project, 'temp_range':range(16, 26), 'item':get_item(project, uid, name), 'msg':msg}
        return render(request, 'bookings/sensibo/device-card.html', context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("guests")
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

        context = {'project':project, 'temp_range':range(16, 26), 'item':get_item(project, uid, name), 'msg':msg}
        return render(request, 'bookings/sensibo/device-card.html', context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


