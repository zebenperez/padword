from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 
from django.urls import reverse

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate, set_session, reverse_cardkey, timestamp_to_date
from padword.decorators import group_required
from .models import *
from .models_lock import *
from .lock_lib import ShLock, get_record_type

import datetime


'''
    Locks
'''
def get_lock_items(request, project_uuid, public=False):
    kwargs = {'project_uuid': project_uuid}

    if public:
        kwargs["private"] = False 

    if "lock_search_alias" in request.session and request.session["lock_search_alias"] != "":
        kwargs["alias__icontains"] = request.session["lock_search_alias"]

    if "lock_search_group" in request.session and request.session["lock_search_group"] != "":
        lg_list = LockGroup.objects.filter(project_uuid=project_uuid, name__icontains=request.session["lock_search_group"]).values_list('uuid', flat=True)
        kwargs["group_uuid__in"] = lg_list

    lock_list = list(Lock.objects.filter(**kwargs))

    if "lock_search_passcode" in request.session and request.session["lock_search_passcode"] != "":
        lock_code = []
        for lock in lock_list:
            item_list = lock.get_all_passcodes()
            for item in item_list:
                if item["keyboardPwd"] == request.session["lock_search_passcode"]: 
                    lock_code.append(lock)
        lock_list = set(lock_list) & set(lock_code)

    if "lock_search_cardcode" in request.session and request.session["lock_search_cardcode"] != "":
        lock_code = []
        for lock in lock_list:
            item_list = lock.get_all_cards()
            for item in item_list:
                if str(item["cardNumber"]) == str(reverse_cardkey(request.session["lock_search_cardcode"])): 
                    lock_code.append(lock)
        lock_list = set(lock_list) & set(lock_code)

    return lock_list 

def get_context(request, project, public=False):
    context = {}
    now = datetime.datetime.now()
    context["project"] = project
    context["tasks"] = LockCron.objects.filter(project_uuid=project.uuid)
    context["items"] = get_lock_items(request, project.uuid, public)
    context["lock_group_list"] = LockGroup.objects.filter(project_uuid=project.uuid)
    context["ini_date"] = now
    context["end_date"] = now + datetime.timedelta(days=7)
    return context

@group_required("admins")
def locks_cron(request, project_id):
    msg = ""
    project = get_or_none(Project, project_id)
    try:
        context = get_context(request, project)
        context["project"] = project
        context["msg"] = msg
        return render (request, "web/locks-cron/locks.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def lock_row(request):
    try:
        item = get_or_none(Lock, request.GET["obj_id"])
        return render(request, "web/locks-cron/lock-list-row.html", {'item': item})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins")
def lock_search(request):
    try:
        #set_lock_filter_session(request)
        #set_session(request, "lock_search_project")
        project_uuid = get_param(request.GET, "project_uuid")
        project = get_or_none(Project, project_uuid, "uuid")

        set_session(request, "lock_search_alias")
        set_session(request, "lock_search_passcode")
        set_session(request, "lock_search_cardcode")
        set_session(request, "lock_search_group")
        #print(request.session["lock_search_cardcode"])

        context = get_context(request, project)
        return render(request, "web/locks-cron/lock-list.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def lock_set_action(request):
    try:
        msg = ""
        errcode = ""

        project_uuid = get_param(request.POST, "project_uuid")
        project = get_or_none(Project, project_uuid, "uuid")
        action = get_param(request.POST, "action")

        value = get_param(request.POST, "value")

        code = reverse_cardkey(get_param(request.POST, "code")) if action == "3" else get_param(request.POST, "code")
        name = get_param(request.POST, "name")
        ini_date = get_param(request.POST, "ini_date", datetime.datetime.now())
        ini_date = datetime.datetime.strptime(ini_date, "%Y-%m-%d") if isinstance(ini_date, str) else ini_date
        end_date = get_param(request.POST, "end_date", datetime.datetime.now() + datetime.timedelta(days=7))
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") if isinstance(end_date, str) else end_date
        ini_date_gmt = project.gmt_date(ini_date)
        end_date_gmt = project.gmt_date(end_date)
        permanent = get_param(request.POST, "permanent")

        lock_group_uuid = get_param(request.POST, "lock_group")

        code_remove = get_param(request.POST, "code_remove")

        lock_list = ""
        for key in request.POST.keys():
            if "ch_" in key and key.split("_")[1] != "0":
                lock_list = "{}{};".format(lock_list, key.split("_")[1])
        if action == "3":
            if permanent != "":
                end_date = datetime.datetime(2099, 12, 31)
            params = "{};{};{};{}".format(code, name, ini_date_gmt, end_date_gmt)
            #params = "{};{};{};{}".format(code, name, ini_date, end_date)
            task = LockCron.objects.create(task="ADD CARD", lock_list=lock_list, params=params, project_uuid=project.uuid)


#        for key in request.POST.keys():
#            try:
#                if "ch_" in key:
#                    lock = get_or_none(Lock, key.split("_")[1])
#                    if lock != None:
#                        if action == "1":
#                            print("Action 1")
#                            #lock.group_uuid = lock_group_uuid
#                            #lock.save()
#                            #lock.set_group()
#                        if action == "2":
#                            print("Action 2")
#                            #if permanent == "":
#                            #    errcode = lock.set_code(code, ini_date, end_date, name)
#                            #elif permanent != "":
#                            #    errcode = lock.set_code(code, ini_date, datetime.datetime(2099, 12, 31), name)
#                        if action == "3":
#                            print("Action 3")
#                            #if permanent == "":
#                            #    errcode = lock.add_card(code, ini_date, end_date, name)
#                            #elif permanent != "":
#                            #    errcode = lock.add_card(code, ini_date, datetime.datetime(2099, 12, 31), name)
#                        if action == "4":
#                            print("Action 4")
#                            #item_list = lock.get_all_passcodes()
#                            #for item in item_list:
#                            #    if item["keyboardPwd"] == code_remove:
#                            #        errcode = lock.remove_code(item["keyboardPwdId"])
#                        if action == "5":
#                            print("Action 5")
#                            #item_list = lock.get_all_cards()
#                            #for item in item_list:
#                            #    if str(item["cardNumber"]) == str(reverse_cardkey(code_remove)): 
#                            #        errcode = lock.remove_card(item["cardId"])
#                        msg = errcode if "Error" in str(errcode) else ""
#            except Exception as e:
#                msg += "<br/>{}".format(e)
#                     
        context = get_context(request, project)
        context["msg"] = msg
        context["project"] = project
        return render (request, "web/locks-cron/locks-content.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def lock_set_task(request):
    try:
        errcode = ""
        task = get_or_none(LockCron, request.GET["obj_id"])
        if task.task == "ADD CARD":
            lock_list = task.lock_list.split(";")
            params = task.params.split(";")
            for lock in lock_list:
                l = get_or_none(Lock, lock)
                if l != None:
                    errcode += l.add_card(params[0], params[2], params[3], params[1])
        return render (request, "web/locks-cron/lock-set-task.html", {'msg': errcode})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

'''
    Locks by project
'''
@group_required("projects")
def locks_tasks_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        context = {"project": project, "tasks": LockCron.objects.filter(project_uuid=project.uuid)}
        return render(request, "web/locks-cron-by-project/tasks.html", context)
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("projects")
def locks_tasks_add(request):
    try:
        project = get_or_none(Project, request.project_id)
        task = LockCron.objects.create(project_uuid=project.uuid)
        return render(request, "web/locks-cron-by-project/task-add-type.html", {"task": task})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("projects")
def locks_tasks_type(request):
    try:
        project = get_or_none(Project, request.project_id)
        task = get_or_none(LockCron, request.GET["obj_id"])
        t = get_param(request.GET, "type")
        task.task = "ADD CARD" if t == "card" else "ADD CODE"
        task.save()
        return render(request, "web/locks-cron-by-project/task-add-params.html", {"task": task, "type": t})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("projects")
def locks_tasks_params(request):
    try:
        project = get_or_none(Project, request.project_id)
        task = get_or_none(LockCron, get_param(request.POST, "obj_id"))
        t = get_param(request.POST, "type")

        code = reverse_cardkey(get_param(request.POST, "code")) if t == "card" else get_param(request.POST, "code")
        name = get_param(request.POST, "name")
        ini_date = get_param(request.POST, "ini_date", datetime.datetime.now())
        ini_date = datetime.datetime.strptime(ini_date, "%Y-%m-%d") if isinstance(ini_date, str) else ini_date
        end_date = get_param(request.POST, "end_date", datetime.datetime.now() + datetime.timedelta(days=7))
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") if isinstance(end_date, str) else end_date
        ini_date_gmt = project.gmt_date(ini_date)
        end_date_gmt = project.gmt_date(end_date)
        permanent = get_param(request.POST, "permanent")

        if permanent != "":
            end_date = datetime.datetime(2099, 12, 31)

        task.params = "{};{};{};{}".format(code, name, ini_date_gmt, end_date_gmt)
        #task.params = "{};{};{};{}".format(code, name, ini_date, end_date)
        task.save()
        items = get_lock_items(request, project.uuid, False)
        return render(request, "web/locks-cron-by-project/task-add-locks.html", {"task": task, "items": items})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("projects")
def locks_tasks_locks(request):
    try:
        project = get_or_none(Project, request.project_id)
        task = get_or_none(LockCron, get_param(request.POST, "obj_id"))

        lock_list = ""
        for key in request.POST.keys():
            if "ch_" in key and key.split("_")[1] != "0":
                lock_list = "{}{};".format(lock_list, key.split("_")[1])

        task.lock_list = lock_list
        task.save()
        return render(request, "web/locks-cron-by-project/task-add-end.html", {"task": task})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})


