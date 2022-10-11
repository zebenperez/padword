from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, get_bool, new_ui_slug, get_items_per_page
from django.db.models import Q
from web.models import Channel, Project, ProjectUser
from contents.models import Category, CategoryUser, ShoppingCart, Item
from user_remote.models import PWUser

from .common_lib import user_in_group
from .models import Form, FormInstance, Status, GuestUser
from guest.models import Guest

import datetime
import logging
import json
logger = logging.getLogger(__name__)

ITEMS_PER_PAGE=get_items_per_page()

'''
    Login
'''
def check_remote_user(user_uuid, api_token, project_uuid):
    obj = PWUser.objects.filter(uuid=user_uuid, api_token=api_token, project_uuid=project_uuid).first()
    return obj

def login(request):
    project_uuid = request.GET["project_uuid"] if "project_uuid" in request.GET else ""
    user_uuid = request.GET["user_uuid"] if "user_uuid" in request.GET else ""
    api_token = request.GET["token"] if "token" in request.GET else ""

    project = Project.objects.filter(uuid=project_uuid).first()
    if project_uuid == "" or project == None:
        return render(request, 'error_exception.html', {'exc': _('Project not found!')})
    if user_uuid == "":
        return render(request, 'error_exception.html', {'exc': _('User not found!')})
    if api_token == "":
        return render(request, 'error_exception.html', {'exc': _('Token not found!')})

    remote_user = check_remote_user(user_uuid, api_token, project_uuid)
    if remote_user == None:
        return render(request, 'error_exception.html', {'exc': _('User not found!')})
    
    user = ProjectUser.get_or_create_project_user(project_uuid, remote_user.email)
    auth.login(request, user)
    return redirect(bookings_by_project, project.id)

'''
    Bookings
'''
def get_booking_context():
    context = {}
    today = datetime.datetime.today()
    ini_date = today + datetime.timedelta(days=-3)
    end_date = today + datetime.timedelta(days=1)
    #edate = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

    items = search("", "", ini_date, end_date.strftime("%Y-%m-%d"), "", "")

    context["ini_date"] = ini_date
    context["end_date"] = end_date
    context["status_list"] = Status.objects.all()
    context['items'] = items[0:ITEMS_PER_PAGE]
    context['total_items'] = len(items)
    return context


#def get_uuid_project_list(user, project, project_uuid):
#    if project_uuid != "":
#        return [project_uuid]
#    if user.groups.filter(name="categories").exists():
#        cat_uuid_list = list(CategoryUser.objects.filter(username=user.username).values_list('category_uuid', flat=True))
#        return list(Category.objects.filter(uuid__in=cat_uuid_list).values_list('project_uuid', flat=True))
#    if user.groups.filter(name="projects").exists():
#        return list(ProjectUser.objects.filter(username=user.username).values_list('project_uuid', flat=True))
#    if project != "":
#        return list(set(Project.objects.filter(name__icontains = project).values_list('uuid', flat=True)))
#    return list(set(Project.objects.all().values_list('uuid', flat=True)))
#
#def filter_search_form_uuid(form, form_uuid, uuid_project_list):
#    if form_uuid != "":
#        return [form_uuid]
#    if form != "":
#        categories_list = list(Category.objects.filter(name__icontains = form).values_list('uuid', flat=True))
#    else:
#        categories_list = list(Category.objects.filter(project_uuid__in = uuid_project_list).values_list('uuid', flat=True))
#    forms_list = list(Form.objects.filter(form_type__order=True, category__in = categories_list).values_list('uuid', flat=True))
#    return forms_list
#
def filter_search_guest(name, uuid_project_list):
    uuid_guests = list(Guest.objects.filter(Q(name__icontains=name) | Q(surname__icontains=name) | Q(email__icontains=name) | Q(mobile__icontains=name) | Q(room=name)).filter(project_id__in = uuid_project_list).values_list('UUID', flat=True))
    return uuid_guests

def filter_search_status(items, status):
    item_list = []
    for item in items:
        if (item.get_status != None and status != "" and item.get_status.status.id == int(status)) or (status == "" and item.get_status != None):
            item_list.append(item)
    return item_list

def filter_search_status_project(items, status, project_uuid):
    item_list = []
    for item in items:
        if item.form.project.uuid == project_uuid:
            if (item.get_status != None and status != "" and item.get_status.status.id == int(status)) or (status == "" and item.get_status != None):
                item_list.append(item)
    return item_list


#def filter_search_project_status(items, project_uuid, status):
#    item_list = []
#    for item in items:
#        if (item.form.get_category.project_uuid == project_uuid):
#            if (item.get_status != None and status != "" and item.get_status.status.id == int(status)) or (status == "" and item.get_status != None):
#                item_list.append(item)
#    return item_list
#
#def search(user, project_uuid, project, form_uuid, form, ini_date, end_date, name, status):
#    uuid_project_list = get_uuid_project_list(user, project, project_uuid)
#    kwargs = {'form_uuid__in': filter_search_form_uuid(form, form_uuid, uuid_project_list)}
#    if ini_date != "":
#        kwargs["date__gte"] = ini_date
#    if end_date != "":
#        ed = end_date.split("-")
#        kwargs["date__lte"] = datetime.datetime(int(ed[0]), int(ed[1]), int(ed[2]), 23, 59, 59)
#    if name != "":
#        kwargs["guest_uuid__in"] = filter_search_guest(name, uuid_project_list)
#
#    items = FormInstance.objects.filter(**kwargs)
#    if project_uuid != "":
#        items = filter_search_project_status(items, project_uuid, status)
#    else:
#        items = filter_search_status(items, status)
#
#    return items
#
##@group_required("admins", "projects", "categories")
#@group_required("admins", "projects")
#def bookings_search(request):
#    try:
#        project = get_param(request.GET, "s-project")
#        project_uuid = get_param(request.GET, "s-project_uuid")
#        form = get_param(request.GET, "s-form")
#        form_uuid = get_param(request.GET, "s-form_uuid")
#        ini_date = get_param(request.GET, "s-ini_date")
#        end_date = get_param(request.GET, "s-end_date")
#        name = get_param(request.GET, "s-name")
#        status = get_param(request.GET, "s-status")
#
#        items = search(request.user, project_uuid, project, form_uuid, form, ini_date, end_date, name, status)
#
#        context={'total_items': len(items), 'items': items[0:ITEMS_PER_PAGE], 'status': status, 'page': 0}
#        return render(request, "bookings/manage/booking-list.html", context)
#    except Exception as e:
#        print (show_exc(e))
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})

def search(project, form, ini_date, end_date, name, status):
    if project != "":
        uuid_project_list = list(set(Project.objects.filter(name__icontains = project).values_list('uuid', flat=True)))
    else:
        uuid_project_list = list(set(Project.objects.all().values_list('uuid', flat=True)))

    if form != "":
        categories_list = list(Category.objects.filter(name__icontains = form).values_list('uuid', flat=True))
    else:
        categories_list = list(Category.objects.filter(project_uuid__in = uuid_project_list).values_list('uuid', flat=True))
    form_list = list(Form.objects.filter(form_type__order=True, category__in = categories_list).values_list('uuid', flat=True))

    kwargs = {'form_uuid__in': form_list}
    if ini_date != "":
        kwargs["date__gte"] = ini_date
    if end_date != "":
        ed = end_date.split("-")
        kwargs["date__lte"] = datetime.datetime(int(ed[0]), int(ed[1]), int(ed[2]), 23, 59, 59)
    if name != "":
        kwargs["guest_uuid__in"] = filter_search_guest(name, uuid_project_list)

    items = FormInstance.objects.filter(**kwargs)
    return filter_search_status(items, status)


@group_required("admins", "projects", "categories", "guests")
#def booking_view(request, fi_id):
def booking_view(request):
    try:
        fi_id = request.GET["obj_id"]
        fi = FormInstance.objects.get(pk = fi_id)
        form = get_or_none(Form, fi.form_uuid, 'uuid')
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk)

        if (fi.get_status != None and fi.get_status.status != None and fi.get_status.status.code == "01") or (fi.get_status is None):
            fi.set_status("02", request.user, "")

        context = {'fi': fi, 'index': "0", 'items':items, 'status_list': Status.objects.all(), 'manage': True}
        return render(request, 'bookings/guest/view-booking.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-fill_form] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects", "guests")
def booking_refresh_status(request, obj_id=None):
    try:
        if not obj_id:
            fi_id = request.GET["obj_id"]
        else:
            fi_id = obj_id
        fi = FormInstance.objects.get(pk = fi_id)
        lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
        json_dict = json.loads(fi.get_status.status.name)
        return HttpResponse(json_dict[lang.upper()])
    except Exception as e:
        print(show_exc(e))
        logger.error("[bookings-fill_form] {}".format(str(e)))
        return HttpResponse("---")
    return HttpResponse("----")

@group_required("admins", "projects")
def booking_refresh(request):
    try:
        fi_id = request.GET["obj_id"]
        fi = FormInstance.objects.get(pk = fi_id)

        context = {'item':fi}
        template = 'bookings/manage/booking-row.html'
        return render(request, template, context)
    except Exception as e:
        print(show_exc(e))
        logger.error("[bookings-fill_form] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def status_form(request):
    try:
        obj = get_or_none(FormInstance, request.GET["obj_id"]) if "obj_id" in request.GET else FormInstance.objects.create()
        return render(request, "bookings/manage/status-form.html", {'obj': obj, 'status_list': Status.objects.all()})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects", "categories")
def change_status(request):
    try:
        if request.POST:
            status_id = request.POST["status"]
            fi_id = request.POST["fi_id"]
            comment = request.POST["comment"]
        else:
            status_id = request.GET["status"]
            fi_id = request.GET["fi_id"]
            comment = request.GET["comment"]

        status = get_or_none(Status, status_id)
        fi = get_or_none(FormInstance, fi_id)
        if status != None and fi != None:
            fi.set_status(status.code, request.user, comment)
            return render(request, "bookings/manage/status-form.html", {'fi': fi, 'status_list': Status.objects.all()})
    except Exception as e:
        print(e)
        logger.error("[bookings-change_status] {}".format(str(e)))
    return render(request, 'error_exception.html', {'exc': 'Status not found!'})

@group_required("admins", "projects", "categories")
def booking_log(request, fi_id):
    try:
        fi = get_or_none(FormInstance, fi_id)
        return render(request, 'bookings/manage/booking-logs.html', {'fi': fi})
    except Exception as e:
        logger.error("[bookings-new_booking] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def bookings_notifications(request, ini_date, end_date):
    try:
        projects_list = list(ProjectUser.objects.filter(username=request.user.username).values_list('project_uuid', flat=True))
        categories_list = list(Category.objects.filter(project_uuid__in = projects_list).values_list('uuid', flat=True))
        forms_list = list(Form.objects.filter(category__in = categories_list).values_list('uuid', flat=True))
        bookings=FormInstance.objects.filter(form_uuid__in=forms_list, date__range=(ini_date, end_date)).order_by('pk')
        total = 0
        for booking in bookings:
            if booking.get_status != None and booking.get_status.status.code == "01":
                total += 1
        e = None
        return HttpResponse(str(total))
    except Exception as e:
        logger.error("[bookings-new_booking] {}".format(str(e)))
        return HttpResponse("0")
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


'''
    ADMINS
'''
@group_required("admins")
def bookings(request):
    try:
        context = get_booking_context()
        context['page'] = 0
        return render (request, "bookings/manage/bookings.html", context)
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
        return render(request, 'full_error_exception.html', {'exc':show_exc(e)})
    return render(request, 'full_error_exception.html', {})

@group_required("admins")
def bookings_search(request):
    try:
        project = get_param(request.GET, "s-project")
        form = get_param(request.GET, "s-form")
        ini_date = get_param(request.GET, "s-ini_date")
        end_date = get_param(request.GET, "s-end_date")
        name = get_param(request.GET, "s-name")
        status = get_param(request.GET, "s-status")

        items = search(project, form, ini_date, end_date, name, status)

        context={'total_items': len(items), 'items': items[0:ITEMS_PER_PAGE], 'status': status, 'page': 0}
        return render(request, "bookings/manage/booking-list.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def bookings_page(request):
    try:
        project = get_param(request.GET, "s-project")
        form = get_param(request.GET, "s-form")
        ini_date = get_param(request.GET, "s-ini_date")
        end_date = get_param(request.GET, "s-end_date")
        name = get_param(request.GET, "s-name")
        status = get_param(request.GET, "s-status")
        page = get_param(request.GET, "s-page", "0")

        items = search(project, form, ini_date, end_date, name, status)

        context={'total_items': len(items), 'items': items[int(page)*ITEMS_PER_PAGE:(int(page) + 1)*ITEMS_PER_PAGE], 'status': status, 'page': page}
        return render(request, "bookings/manage/booking-page.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def booking_preview(request, form_uuid):
    try:
        form = get_or_none(Form, form_uuid, "uuid")
        if form == None:
            return render(request, 'error_exception.html', {'exc': _('Form not found!')})
        
        context = {'form': form, 'index': "0", "ro": False,}
        return render(request, 'bookings/show-category.html', context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-new_booking] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

'''
    Project users
'''
def pr_search(project_uuid, form, ini_date, end_date, name, status):
    if form != "":
        categories_list = list(Category.objects.filter(project_uuid = project_uuid, name__icontains = form).values_list('uuid', flat=True))
    else:
        categories_list = list(Category.objects.filter(project_uuid = project_uuid).values_list('uuid', flat=True))
    categories_list2 = Category.objects.filter(project_uuid = project_uuid)
    form_list = list(Form.objects.filter(form_type__order=True, category__in = categories_list).values_list('uuid', flat=True))
    form_list2 = Form.objects.filter(form_type__order=True, category__in = categories_list)

    kwargs = {'form_uuid__in': form_list}
    if ini_date != "":
        kwargs["date__gte"] = ini_date
    if end_date != "":
        ed = end_date.split("-")
        kwargs["date__lte"] = datetime.datetime(int(ed[0]), int(ed[1]), int(ed[2]), 23, 59, 59)
    if name != "":
        kwargs["guest_uuid__in"] = filter_search_guest(name, [project_uuid])

    items = FormInstance.objects.filter(**kwargs)
    return filter_search_status_project(items, status, project_uuid)

def get_booking_project_context(project):
    context = {}
    today = datetime.datetime.today()
    ini_date = today + datetime.timedelta(days=-3)
    end_date = today + datetime.timedelta(days=1)
    #edate = datetime.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
            
    items = pr_search(project.uuid, "", ini_date, end_date.strftime("%Y-%m-%d"), "", "")

    context["project_uuid"] = project.uuid
    context["project_name"] = project.name
    context["ini_date"] = ini_date
    context["end_date"] = end_date
    context["status_list"] = Status.objects.all()
    context['items'] = items[0:ITEMS_PER_PAGE]
    context['total_items'] = len(items)
    return context

@group_required("projects")
def bookings_pr_search(request):
    try:
        project_uuid = get_param(request.GET, "s-project_uuid")
        form = get_param(request.GET, "s-form")
        ini_date = get_param(request.GET, "s-ini_date")
        end_date = get_param(request.GET, "s-end_date")
        name = get_param(request.GET, "s-name")
        status = get_param(request.GET, "s-status")

        items = pr_search(project_uuid, form, ini_date, end_date, name, status)

        context={'total_items': len(items), 'items': items[0:ITEMS_PER_PAGE], 'status': status, 'page': 0}
        return render(request, "bookings/cat-manage/booking-list.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("projects")
def bookings_pr_page(request):
    try:
        project_uuid = get_param(request.GET, "s-project_uuid")
        form = get_param(request.GET, "s-form")
        ini_date = get_param(request.GET, "s-ini_date")
        end_date = get_param(request.GET, "s-end_date")
        name = get_param(request.GET, "s-name")
        status = get_param(request.GET, "s-status")
        page = get_param(request.GET, "s-page", "0")

        items = pr_search(project_uuid, form, ini_date, end_date, name, status)

        context={'total_items': len(items), 'items': items[int(page)*ITEMS_PER_PAGE:(int(page) + 1)*ITEMS_PER_PAGE], 'status': status, 'page': page}
        return render(request, "bookings/cat-manage/booking-page.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


@group_required("projects")
def bookings_by_project(request, project_id):
    try:
        if project_id == -1:
            return render(request, 'error_exception.html', {'exc': _('Project not found!')})
        context = get_booking_project_context(get_or_none(Project, project_id))
        context['page'] = 0
        return render (request, "bookings/pr-manage/bookings.html", context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-bookings_by_project] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

'''
    Category users
'''
def cat_search(project_uuid, category_user, form, ini_date, end_date, name, status):
    if form == "":
        categories = [item.uuid for item in category_user.categories]
        form_list = list(Form.objects.filter(category__in=categories).distinct().values_list("uuid", flat=True))
    else:
        form_list = [form]
    kwargs = {'form_uuid__in': form_list}
    if ini_date != "":
        kwargs["date__gte"] = ini_date
    if end_date != "":
        ed = end_date.split("-")
        kwargs["date__lte"] = datetime.datetime(int(ed[0]), int(ed[1]), int(ed[2]), 23, 59, 59)
    if name != "":
        kwargs["guest_uuid__in"] = filter_search_guest(name, [project_uuid])

    items = FormInstance.objects.filter(**kwargs)
    return filter_search_status_project(items, status, project_uuid)

def get_booking_category_context(project, category_user, form_list):
    context = {}
    today = datetime.datetime.today()
    ini_date = today + datetime.timedelta(days=-3)
    end_date = today + datetime.timedelta(days=1)

    items = cat_search(project.uuid, category_user, "", ini_date, end_date.strftime("%Y-%m-%d"), "", "")

    context["project_uuid"] = project.uuid
    context["project_name"] = project.name
    context["form_list"] = form_list
    context["ini_date"] = ini_date
    context["end_date"] = end_date
    context["status_list"] = Status.objects.all()
    context["items"] = items
    context['items'] = items[0:ITEMS_PER_PAGE]
    context['total_items'] = len(items)
    return context

@group_required("categories")
def bookings_cat_search(request):
    try:
        project_uuid = get_param(request.GET, "s-project_uuid")
        form = get_param(request.GET, "s-form")
        #form_uuid = get_param(request.GET, "s-form_uuid")
        ini_date = get_param(request.GET, "s-ini_date")
        end_date = get_param(request.GET, "s-end_date")
        name = get_param(request.GET, "s-name")
        status = get_param(request.GET, "s-status")

        items = cat_search(project_uuid, request.category_user, form, ini_date, end_date, name, status)

        context={'total_items': len(items), 'items': items[0:ITEMS_PER_PAGE], 'status': status, 'page': 0}
        return render(request, "bookings/cat-manage/booking-list.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("categories")
def bookings_cat_page(request):
    try:
        project_uuid = get_param(request.GET, "s-project_uuid")
        form = get_param(request.GET, "s-form")
        #form_uuid = get_param(request.GET, "s-form_uuid")
        ini_date = get_param(request.GET, "s-ini_date")
        end_date = get_param(request.GET, "s-end_date")
        name = get_param(request.GET, "s-name")
        status = get_param(request.GET, "s-status")
        page = get_param(request.GET, "s-page", "0")

        items = cat_search(project_uuid, request.category_user, form, ini_date, end_date, name, status)

        context={'total_items': len(items), 'items': items[int(page)*ITEMS_PER_PAGE:(int(page) + 1)*ITEMS_PER_PAGE], 'status': status, 'page': page}
        return render(request, "bookings/cat-manage/booking-page.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("categories")
def bookings_by_category(request):
    try:
        categories = [item.uuid for item in request.category_user.categories]
        form_list = Form.objects.filter(category__in=categories).distinct()
        if len(form_list) == 0 or len(categories) == 0:
            return render(request, 'error_exception.html', {'exc': _('Form not found!')})
        project = request.category_user.categories[0].project

        context = get_booking_category_context(project, request.category_user, form_list)
        context['page'] = 0
        return render (request, "bookings/cat-manage/bookings.html", context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-bookings_by_project] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("categories")
def form_edit_category_user(request):
    try:
        # Create or edit by category
        if "obj_id" in request.GET:
            uuid = request.GET["obj_id"]
            cat = get_or_none(Category, uuid, 'uuid')
            if cat == None:
                return render(request, 'error_exception.html', {'exc': _('Category not found!')})
            obj = get_or_none(Form, cat.uuid, 'category')
            #if obj == None:
            #    obj = Form.objects.create(uuid=new_ui_slug(Form), category=cat.uuid)
        # New form
        else:
            return render(request, 'error_exception.html', {'exc': _('Category not found!')})
            #obj = Form.objects.create(uuid=new_ui_slug(Form))

        context = {
            'obj': obj,
            #'block_list': Block.objects.all(),
            #'form_type_list': FormType.objects.all(),
            #'answer_type_list': AnswerType.objects.all(),
            #'question_type_list': QuestionType.objects.all()
        }

        return render(request, "forms/form-edit-category.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})



'''
    Test
'''
@login_required
def test(request):
    return HttpResponse("OK")

