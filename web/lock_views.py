from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 
from django.urls import reverse

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate, set_session, reverse_cardkey, timestamp_to_date
from padword.decorators import group_required
from .models import *
from .models_lock import *
from .lock_lib import ShLock, get_record_type
from guest.models import KeyCode, KeyCard, Guest

import csv, requests, threading
import time, datetime, pytz


'''
    Locks
'''
def remove_lock(lock):
    KeyCode.objects.filter(lock=lock.uuid).delete()
    KeyCard.objects.filter(lock=lock.uuid).delete()
    lock.delete()

def update_locks(project):
    sh_lock = ShLock(project.lock_access_token)

    current_locks = []
    for item in sh_lock.get_lock_all():
        uuid=item["lockId"]
        lock, created = Lock.objects.get_or_create(uuid=uuid, project_uuid=project.uuid)
        lock.alias = item["lockAlias"]
        if created:
            lock.last_update = pytz.utc.localize(datetime.datetime.now())
        lock.save()
        if uuid not in current_locks:
            current_locks.append(uuid)

    lock_list = Lock.objects.filter(project_uuid=project.uuid).exclude(uuid__in = current_locks)
    for lock in lock_list:
        remove_lock(lock)

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
            if request.session["lock_search_passcode"] in lock.code_cache:
                lock_code.append(lock)
#            item_list = lock.get_all_passcodes()
#            for item in item_list:
#                if item["keyboardPwd"] == request.session["lock_search_passcode"]: 
#                    lock_code.append(lock)
        lock_list = set(lock_list) & set(lock_code)

    if "lock_search_cardcode" in request.session and request.session["lock_search_cardcode"] != "":
        lock_code = []
        for lock in lock_list:
            card_code = reverse_cardkey(request.session["lock_search_cardcode"]) 
            if str(card_code) in str(lock.card_cache):
                lock_code.append(lock)
#            item_list = lock.get_all_cards()
#            for item in item_list:
#                if str(item["cardNumber"]) == str(reverse_cardkey(request.session["lock_search_cardcode"])): 
#                    lock_code.append(lock)
        lock_list = set(lock_list) & set(lock_code)

    return lock_list 

def get_context(request, project, public=False):
    context = {}
    now = datetime.datetime.now()
    context["project"] = project
    context["items"] = get_lock_items(request, project.uuid, public)
    context["lock_group_list"] = LockGroup.objects.filter(project_uuid=project.uuid)
    context["ini_date"] = now
    context["end_date"] = now + datetime.timedelta(days=7)
    return context

@group_required("admins")
#def locks(request):
def locks_by_project(request, project_id):
    msg = ""
    project = get_or_none(Project, project_id)
    try:
        update_locks(project)
    except Exception as e:
        print(e)
        msg = e
 
    try:
        context = get_context(request, project)
        context["project"] = project
        context["msg"] = msg
        return render (request, "web/locks/locks.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def lock_row(request):
    try:
        item = get_or_none(Lock, request.GET["obj_id"])
        return render(request, "web/locks/lock-list-row.html", {'item': item})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins")
def lock_search(request):
    try:
        #set_lock_filter_session(request)
        #set_session(request, "lock_search_project")
        project_uuid = get_param(request.GET, "project_uuid")
        project = get_or_none(Project, project_uuid, "uuid")
        lock_list = get_param(request.GET, "list")
        card_code = reverse_cardkey(get_param(request.GET, "lock_search_cardcode")) 

        if lock_list == "":
            set_session(request, "lock_search_alias")
            set_session(request, "lock_search_passcode")
            set_session(request, "lock_search_cardcode", card_code)
            set_session(request, "lock_search_group")
            #print(request.session["lock_search_cardcode"])

        context = get_context(request, project)
        return render(request, "web/locks/lock-list.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def lock_form(request):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/locks/lock-form.html", {'obj': obj,})

@group_required("admins")
def lock_remove(request):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        project = obj.project
        #obj.delete()
        remove_lock(obj)
    context = get_context(request, project)
    return render (request, "web/locks/lock-list.html", context)

@group_required("admins")
def lock_get_all_passcodes(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/locks/lock-all-passcodes.html", {'obj': obj,})

@group_required("admins", "projects")
def lock_remove_code(request):
    try:
        lock = get_or_none(Lock, request.GET["obj_id"])
        code_id = request.GET["code_id"]
        code = get_param(request.GET, "code")

        errcode = lock.remove_code(code_id, code)
        msg = errcode if "Error" in str(errcode) else ""
 
        return HttpResponse("")
        #return render(request, "web/locks/lock-all-cards.html", {'obj': lock,})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def lock_remove_all_passcodes(request, obj_id=None):
    try:
        lock = get_or_none(Lock, request.GET["obj_id"])
        err = ""
        for code in lock.get_all_passcodes():
            err2 = lock.remove_code(code["keyboardPwdId"], code["keyboardPwd"])
            if err2 != 0:
                err += "Code {}: {}<br/>".format(code["keyboardPwd"], err2)
        return render(request, "web/locks/lock-all-passcodes.html", {'obj': lock, "err": err})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins")
def lock_get_all_cards(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/locks/lock-all-cards.html", {'obj': obj,})

@group_required("admins", "projects")
def lock_remove_card(request):
    try:
        lock = get_or_none(Lock, request.GET["obj_id"])
        card_id = request.GET["card_id"]
        card = get_param(request.GET, "card")

        errcode = lock.remove_card(card_id, card)
        return HttpResponse("")
        #return render(request, "web/locks/lock-all-cards.html", {'obj': lock,})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def lock_remove_all_cards(request, obj_id=None):
    try:
        lock = get_or_none(Lock, request.GET["obj_id"])
        err = ""
        for code in lock.get_all_cards():
            err2 = lock.remove_card(code["cardId"], code["cardNumber"])
            if err2 != 0:
                err += "Code {}: {}<br/>".format(code["cardNumber"], err2)
        return render(request, "web/locks/lock-all-cards.html", {'obj': lock, 'err': err})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins")
def lock_get_all_records(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/locks/lock-all-records.html", {'obj': obj,})


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

        for key in request.POST.keys():
            try:
                if "ch_" in key:
                    lock = get_or_none(Lock, key.split("_")[1])
                    if lock != None:
                        if action == "1":
                            lock.group_uuid = lock_group_uuid
                            lock.save()
                            lock.set_group()
                        if action == "2":
                            #if permanent == "" and one == "":
                            if permanent == "":
                                errcode = lock.set_code(code, ini_date_gmt, end_date_gmt, name)
                                #errcode = lock.set_code(code, ini_date, end_date, name)
                            elif permanent != "":
                                errcode = lock.set_code(code, ini_date_gmt, datetime.datetime(2099, 12, 31), name)
                                #errcode = lock.set_code(code, ini_date, datetime.datetime(2099, 12, 31), name)
                            print(errcode)
                            #elif one != "":
                            #    errcode = lock.get_code(1, ini_date, end_date)
                        if action == "3":
                            if permanent == "":
                                errcode = lock.add_card(code, ini_date_gmt, end_date_gmt, name)
                                #errcode = lock.add_card(code, ini_date, end_date, name)
                            elif permanent != "":
                                errcode = lock.add_card(code, ini_date_gmt, datetime.datetime(2099, 12, 31), name)
                                #errcode = lock.add_card(code, ini_date, datetime.datetime(2099, 12, 31), name)
                        if action == "4":
                            item_list = lock.get_all_passcodes()
                            for item in item_list:
                                if item["keyboardPwd"] == code_remove:
                                    errcode = lock.remove_code(item["keyboardPwdId"], item["keyboardPwd"])
                        if action == "5":
                            item_list = lock.get_all_cards()
                            for item in item_list:
                                if str(item["cardNumber"]) == str(reverse_cardkey(code_remove)): 
                                    errcode = lock.remove_card(item["cardId"], item["cardNumber"])
                        msg = errcode if "Error" in str(errcode) else ""
            except Exception as e:
                msg += "<br/>{}".format(e)
                     
        context = get_context(request, project)
        context["msg"] = msg
        context["project"] = project
        return render (request, "web/locks/locks-content.html", context)
        #return render(request, "web/locks/lock-list.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def lock_share_code(request):
    try:
        lock = get_or_none(Lock, request.GET["obj_id"])
        code = request.GET["code"]

        plu = get_or_none(ProjectLockUser, lock.project.uuid, "project_uuid")
        alias = lock.room_obj.alias if lock.room_obj != None else ""
        text = plu.text_to_share.replace("__CODE__",code).replace("__ROOM__",lock.room).replace("__ALIAS__",alias).replace("__PHONE__","").replace("__NAME__","").replace("__SURNAME__","")
        return render(request, "web/locks/share-modal-body.html", {"text": text})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins", "projects")
def lock_share_code_guest(request):
    try:
        guest = get_or_none(Guest, request.GET["obj_id"])
        key_code = guest.keycodes.all().first()
        code = key_code.code if key_code != None else ""

        plu = get_or_none(ProjectLockUser, guest.project.uuid, "project_uuid")
        alias = guest.room_obj.alias if guest.room_obj != None else ""
        text = plu.text_to_share.replace("__CODE__",code).replace("__ROOM__",guest.room).replace("__ALIAS__",alias).replace("__PHONE__",guest.mobile).replace("__NAME__",guest.name).replace("__SURNAME__",guest.surname)
        pwa_url = request.build_absolute_uri(reverse("guest-access-auto", kwargs = {'guest_uuid': guest.UUID}))
        text = text.replace("__URLPWA__", pwa_url)
        return render(request, "web/locks/share-modal-body.html", {"guest": guest, "text": text})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("admins")
def lock_update_params(request):
    lock = get_or_none(Lock, request.GET["obj_id"])
    lock.update_params()
    return render(request, "web/locks/lock-list-row.html", {"item": lock})

@group_required("admins")
def lock_set_group(request):
    try:
        value = request.GET["value"]
        lock = get_or_none(Lock, request.GET["obj_id"])
        lock.group_uuid = value
        lock.save()
        lock.set_group()
        return HttpResponse(_("Saved!"))
    except Exception as e:
        return HttpResponse("Error: {}".format(e))

@group_required("admins", "projects")
def lock_export_csv(request, lock_id):
    try:
        lock = get_or_none(Lock, lock_id)
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}_{}.csv"'.format(lock.project.name, lock.alias)},
        )

        writer = csv.writer(response)
        writer.writerow(['Record type', 'Success', 'Username', 'Code', 'Lock date', 'Server date'])
        for item in lock.get_all_records():
            item_type = get_record_type(item["recordType"])
            success = _("Yes") if item["success"] == 1 else _("No")
            lock_date = timestamp_to_date(item["lockDate"])
            server_date = timestamp_to_date(item["serverDate"])
            writer.writerow([item_type, success, item["username"], item["keyboardPwd"], lock_date, server_date])
        return response
    except Exception as e:
        return HttpResponse("Error: {}".format(e))

@group_required("admins", "projects")
def lock_export_pdf(request, lock_id):
    try:
        lock = get_or_none(Lock, lock_id)
        return render(request, "web/locks/lock-records-print.html", {'obj': lock,})
    except Exception as e:
        return HttpResponse("Error: {}".format(e))

'''
    Locks for "projects" users
'''
@group_required("projects")
def locks_by_project2(request):
    try:
        project = get_or_none(Project, request.project_id)
        context = get_context(request, project, True)
        context["project"] = project
        context["active"] = 'locks'
        return render(request, "web/locks-by-project/locks.html", context)
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("projects")
def lock_row_by_project(request):
    try:
        item = get_or_none(Lock, request.GET["obj_id"])
        return render(request, "web/locks-by-project/lock-list-row.html", {'item': item})
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("projects")
def lock_search_by_project(request):
    try:
        project = get_or_none(Project, request.project_id)
        lock_list = get_param(request.GET, "list")
        card_code = reverse_cardkey(get_param(request.GET, "lock_search_cardcode")) 

        if lock_list == "":
            set_session(request, "lock_search_alias")
            set_session(request, "lock_search_passcode")
            set_session(request, "lock_search_cardcode", card_code)
            set_session(request, "lock_search_group")

        context = get_context(request, project, True)
        return render(request, "web/locks-by-project/lock-list.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def lock_update_params_by_project(request):
    lock = get_or_none(Lock, request.GET["obj_id"])
    lock.update_params()
    return render(request, "web/locks-by-project/lock-list-row.html", {"item": lock})

@group_required("projects")
def lock_get_all_passcodes_by_project(request):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/locks-by-project/lock-all-passcodes.html", {'obj': obj,})

@group_required("projects")
def lock_get_all_cards_by_project(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/locks-by-project/lock-all-cards.html", {'obj': obj,})

@group_required("projects")
def lock_get_all_records_by_project(request, obj_id=None):
    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj == None:
        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
    return render(request, "web/locks-by-project/lock-all-records.html", {'obj': obj,})

@group_required("projects")
def lock_set_action_by_project(request):
    try:
        msg = ""
        errcode = ""

        project = get_or_none(Project, request.project_id)
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

        code_remove = get_param(request.POST, "code_remove")

        for key in request.POST.keys():
            try:
                if "ch_" in key:
                    lock = get_or_none(Lock, key.split("_")[1])
                    if lock != None:
                        if action == "2":
                            if permanent == "":
                                errcode = lock.set_code(code, ini_date_gmt, end_date_gmt, name)
                                #errcode = lock.set_code(code, ini_date, end_date, name)
                            elif permanent != "":
                                errcode = lock.set_code(code, ini_date_gmt, datetime.datetime(2099, 12, 31), name)
                                #errcode = lock.set_code(code, ini_date, datetime.datetime(2099, 12, 31), name)
                        if action == "3":
                            if permanent == "":
                                errcode = lock.add_card(code, ini_date_gmt, end_date_gmt, name)
                                #errcode = lock.add_card(code, ini_date, end_date, name)
                            elif permanent != "":
                                errcode = lock.add_card(code, ini_date_gmt, datetime.datetime(2099, 12, 31), name)
                                #errcode = lock.add_card(code, ini_date, datetime.datetime(2099, 12, 31), name)
                        if action == "4":
                            item_list = lock.get_all_passcodes()
                            for item in item_list:
                                if item["keyboardPwd"] == code_remove:
                                    errcode = lock.remove_code(item["keyboardPwdId"], item["keyboardPwd"])
                        if action == "5":
                            item_list = lock.get_all_cards()
                            for item in item_list:
                                if str(item["cardNumber"]) == str(reverse_cardkey(code_remove)): 
                                    errcode = lock.remove_card(item["cardId"], item["cardNumber"])
                        msg = errcode if "Error" in str(errcode) else ""
            except Exception as e:
                msg += "<br/>{}".format(e)
                 
        context = get_context(request, project, True)
        context["msg"] = msg
        #return redirect(locks_by_project2)
        context["project"] = project
        return render (request, "web/locks-by-project/locks-content.html", context)
        #return render(request, "web/locks-by-project/locks.html", context)
        #return render(request, "web/locks-by-project/lock-list.html", context)
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

#@group_required("projects")
def locks_update_info_back():
    lock_list = Lock.objects.all()
    for lock in lock_list:
        if lock.project != None:
            lock.update_params()

def locks_update_info(request, code):
    #lock_list = Lock.objects.filter(project_uuid = request.GET["uuid"])
    #lock_list = Lock.objects.filter(project_uuid = uuid)
    if code == "i2mrkme-fiWQFEF23qd4F4f-cwe3323r-fWQWEf":
        t = threading.Thread(target=locks_update_info_back, args=[], daemon=True)
        t.start()
    return HttpResponse("--OK--")

@group_required("admins", "projects")
def locks_open(request):
    lock = get_or_none(Lock, request.GET["obj_id"])
    msg = lock.open_lock()
    msg = msg if msg != True else ""
    return render (request, "web/locks/lock-open.html", {"msg": msg, "lock": lock.id})
    #return HttpResponse(msg)

#@group_required("admins")
#def lock_get_cards(request):
#    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
#    url = 'https://euapi.ttlock.com/v3/identityCard/list'
#    if obj is None:
#        list_obj = Lock.objects.all()
#    else:
#        list_obj = [obj]
#
#    for obj in list_obj:
#        params = dict(
#            clientId='c5cd9353990e4061a082a7a275897de1',
#            accessToken='4719a3f737f7d1adafe139fbea20f6fb',
#            lockId=int(obj.uuid),
#            pageNo=1,
#            pageSize=100,
#            date = int(round(datetime.datetime.now().timestamp() * 1000))
#        )
#        resp = requests.get(url=url, params=params)
#        data = resp.json() # Check the JSON Response Content documentation below
#        for keycard_json in data['list']:
#            keycard = KeyCard.objects.get(bluetooth = keycard_json['cardNumber'])
#            keycard.lock = obj
#            keycard.save()
#
#    return HttpResponse("OK")
#


#'''
#    EKeys
#'''
#@group_required("admins")
#def ekeys(request):
#    URL = "https://app.tullaveonline.com"
#    URL2 = "https://app.tullaveonline.com/?controller=login"
#    URL3 = "https://app.tullaveonline.com/?controller=precheckin"
#    client = requests.session()
#    page = client.get(URL)
#    login_data = dict(usuario="admin", password="admin", action="dologin")
#    r = client.post(URL2, data=login_data, headers=dict(Referer=URL))
#    page = client.get(URL3)
#    return render (request, "web/ekeys.html", {'page': page.text.replace('src="js/', 'src="https://app.millaveonline.com/js/')})
#

