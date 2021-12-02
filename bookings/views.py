from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, get_bool, new_ui_slug
from django.db.models import Q
from web.models import Channel, Project, ProjectUser
from contents.models import Category, ShoppingCart, Item
from user_remote.models import PWUser

from .common_lib import write_log, user_in_group
from .models import Form, FormInstance, Status, GuestUser
from guest.models import Guest

import datetime
import logging
import json
logger = logging.getLogger(__name__)

ITEMS_PER_PAGE=20

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
def get_booking_context(form=None, project=None):
    context = {}
    today = datetime.datetime.today()
    ini_date = today + datetime.timedelta(days=-3)

    kwargs = {'date__gte': ini_date, 'date__lte': today+datetime.timedelta(days=1)}
    if form != None:
        kwargs['form_uuid'] = form.uuid
        context["form_name"] = form.name
        if form.channels.all().count() == 1:
            fc = form.channels.first()
            channel = Channel.objects.filter(uuid = fc.channel).first()
            context["channel_name"] = channel.name
            context["project_name"] = channel.project.name

    if project != None:
        uuid_list = [item.uuid for item in Category.objects.filter(project_uuid=project.uuid)]
        forms_uuid_list = [item.uuid for item in Form.objects.filter(category__in = uuid_list)]
        kwargs["form_uuid__in"] = forms_uuid_list
        context["project_name"] = project.name

    items = FormInstance.objects.filter(**kwargs)
    if items.count() == 0 and project == None:
        context["msg"] = 'There are no results for the search. Here the last 100 reservations.'
        items = FormInstance.objects.all()[:100]

    context["ini_date"] = ini_date
    context["end_date"] = today + datetime.timedelta(days=1)
    context["status_list"] = Status.objects.all()
    context["items"] = items
    return context

@group_required("admins", "projects")
def bookings_by_project(request, project_id):
    try:
        if project_id == -1:
            return render(request, 'error_exception.html', {'exc': _('Project not found!')})
        context = get_booking_context(project=get_or_none(Project, project_id))
        context['total_items'] = context['items'].count()
        context['items'] = context['items'][0:ITEMS_PER_PAGE]
        context['page'] = 0
        return render (request, "bookings/manage/bookings.html", context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-bookings_by_project] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def bookings_search(request):
    try:
        project = get_param(request.GET, "s-project")
        channel = get_param(request.GET, "s-channel")
        form = get_param(request.GET, "s-form")
        ini_date = get_param(request.GET, "s-ini_date")
        end_date = get_param(request.GET, "s-end_date")
        name = get_param(request.GET, "s-name")
        status = get_param(request.GET, "s-status")

        kwargs = {}
        uuid_projects = None
        if request.user.groups.filter(name="projects").exists():
            uuid_projects_list = list(ProjectUser.objects.filter(username=request.user.username).values_list('project_uuid', flat=True))
            uuid_projects_list = list(set(uuid_projects_list) & set(Project.objects.filter(name__icontains = project).values_list('uuid', flat=True)))
            categories_list = list(Category.objects.filter(project_uuid__in = uuid_projects_list).values_list('uuid', flat=True))
            forms_list = list(Form.objects.filter(category__in = categories_list).values_list('uuid', flat=True))
            kwargs["form_uuid__in"] = forms_list
        else:
            if project != "":
                uuid_projects_list = list(set(Project.objects.filter(name__icontains = project).values_list('uuid', flat=True)))
                categories_list = list(Category.objects.filter(project_uuid__in = uuid_projects_list).values_list('uuid', flat=True))
                forms_list = list(Form.objects.filter(category__in = categories_list).values_list('uuid', flat=True))
                kwargs["form_uuid__in"] = forms_list

        if form != "":
            uuid_list = list(set(Form.objects.filter(name__icontains=form).values_list('uuid', flat=True)))
            kwargs["form_uuid__in"] = uuid_list
        if ini_date != "":
            kwargs["date__gte"] = ini_date
        if end_date != "":
            ed = end_date.split("-")
            kwargs["date__lte"] = datetime.datetime(int(ed[0]), int(ed[1]), int(ed[2]), 23, 59, 59)
        if name != "":
            uuid_guests = Guest.objects.filter(Q(name__icontains = name) | Q(surname__icontains=name) | Q(email__icontains=name) | Q(mobile__icontains=name) | Q(room=name)) 
            if uuid_projects_list:
                guests_in_projects = GuestUser.objects.filter(project_uuid__in = uuid_projects_list).values_list('guest_uuid', flat=True)
                uuid_guests = list(set(uuid_guests.values_list('UUID', flat=True)) & set(guests_in_projects))
            else:
                uuid_guests = list(set(uuid_guests.values_list('UUID', flat=True)))
            kwargs["guest_uuid__in"] = uuid_guests

        if status != "":
            kwargs["status__pk"] = status

        items = FormInstance.objects.filter(**kwargs)
        context={}
        context['total_items'] = items.count()
        context['items'] = items[0:ITEMS_PER_PAGE]
        context['status'] = status
        context['page'] = 0

        return render(request, "bookings/manage/booking-list.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects", "guests")
#def booking_view(request, fi_id):
def booking_view(request):
    try:
        fi_id = request.GET["obj_id"]
        fi = FormInstance.objects.get(pk = fi_id)
        form = get_or_none(Form, fi.form_uuid, 'uuid')
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk)

        if (fi.status != None and fi.status.code == "01") or (fi.status is None):
            if fi.status is not None:
                previous_status = fi.status.name
            else:
                previous_status = 'None'
            fi.set_status("02")
            write_log(request.user, fi, _("Status change from {} to {}".format(previous_status, fi.status.name)))

        context = {'fi': fi, 'index': "0", 'items':items, 'status_list': Status.objects.all()}
        if fi.form and fi.form.form_type:
            template = 'bookings/view-booking-project.html' if fi.form.form_type.code == "ecom" else 'bookings/view-booking.html'
        else:
            template = 'bookings/view-booking.html'
        return render(request, template, context)
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
        json_dict = json.loads(fi.status.name)
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

@group_required("admins", "projects")
def change_status(request):
    try:
        if request.POST:
            status_id = request.POST["status"]
            fi_id = request.POST["fi_id"]
        else:
            status_id = request.GET["status"]
            fi_id = request.GET["fi_id"]

        status = get_or_none(Status, status_id)
        fi = get_or_none(FormInstance, fi_id)
        if status != None and fi != None:
            previous_status = fi.status.name if fi.status != None else "Created"
            fi.set_status(status.code)
            write_log(request.user, fi, _("Status change from {} to {}".format(previous_status, fi.status.name)))
            if request.POST:
                return redirect(bookings_by_form, fi.form.id)
            return render(request, "bookings/manage/status-links.html", {'fi': fi, 'status_list': Status.objects.all()})
    except Exception as e:
        print(e)
        logger.error("[bookings-change_status] {}".format(str(e)))
    return render(request, 'error_exception.html', {'exc': 'Status not found!'})

@group_required("admins", "projects")
def booking_log(request, fi_id):
    try:
        fi = get_or_none(FormInstance, fi_id)
        return render(request, 'bookings/manage/booking-logs.html', {'fi': fi})
    except Exception as e:
        logger.error("[bookings-new_booking] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def bookings_notifications(request):
    try:
        projects_list = list(ProjectUser.objects.filter(username=request.user.username).values_list('project_uuid', flat=True))
        categories_list = list(Category.objects.filter(project_uuid__in = projects_list).values_list('uuid', flat=True))
        forms_list = list(Form.objects.filter(category__in = categories_list).values_list('uuid', flat=True))
        bookings = FormInstance.objects.filter(form_uuid__in = forms_list, status__code = "01" ).order_by('pk')
        e = None
        return HttpResponse(str(bookings.count()))
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
        if request.user.groups.filter(name='admin').exists():
            context = get_booking_context()
        else:
            context = get_booking_context()
        context['total_items'] = context['items'].count()
        context['items'] = context['items'][0:ITEMS_PER_PAGE]
        context['page'] = 0
        return render (request, "bookings/manage/bookings.html", context)
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
        return render(request, 'full_error_exception.html', {'exc':show_exc(e)})
    return render(request, 'full_error_exception.html', {})

@group_required("admins", "projects")
def bookings_page(request):
    try:
        project = get_param(request.GET, "s-project")
        channel = get_param(request.GET, "s-channel")
        form = get_param(request.GET, "s-form")
        ini_date = get_param(request.GET, "s-ini_date")
        end_date = get_param(request.GET, "s-end_date")
        name = get_param(request.GET, "s-name")
        status = get_param(request.GET, "s-status")
        page = get_param(request.GET, "s-page", "0")

        kwargs = {}
        if request.user.groups.filter(name="projects").exists():
            uuid_projects_list = list(ProjectUser.objects.filter(username=request.user.username).values_list('project_uuid', flat=True))
            uuid_projects_list = list(set(uuid_projects_list) & set(Project.objects.filter(name__icontains = project).values_list('uuid', flat=True)))
            categories_list = list(Category.objects.filter(project_uuid__in = uuid_projects_list).values_list('uuid', flat=True))
            forms_list = list(Form.objects.filter(category__in = categories_list).values_list('uuid', flat=True))
            kwargs["form_uuid__in"] = forms_list
        else:
            if project != "":
                uuid_channel_list = [item.uuid for item in Channel.objects.filter(project__name__icontains=project)]
                uuid_list = [item.uuid for item in Form.objects.filter(channels__channel__in=uuid_channel_list)]
                kwargs["form_uuid__in"] = uuid_list
                #kwargs["form__channels__channel__in"] = uuid_list
            if channel != "":
                uuid_channel_list = [item.uuid for item in Channel.objects.filter(name__icontains=channel)]
                uuid_list = [item.uuid for item in Form.objects.filter(channels__channel__in=uuid_channel_list)]
                kwargs["form_uuid__in"] = uuid_list
                #kwargs["form__channels__channel__in"] = uuid_list
        if form != "":
            uuid_list = [item.uuid for item in Form.objects.filter(name__icontains=form)]
            kwargs["form_uuid__in"] = uuid_list
            #kwargs["form__name__icontains"] = form
        if ini_date != "":
            kwargs["date__gte"] = ini_date
        if end_date != "":
            #kwargs["date__lte"] = end_date
            ed = end_date.split("-")
            kwargs["date__lte"] = datetime.datetime(int(ed[0]), int(ed[1]), int(ed[2]), 23, 59, 59)
        if name != "":
            uuid_guests = Guest.objects.filter(name__icontains = name) or Guest.objects.filter(surname__icontains=name)
            uuid_guests = set(uuid_guests.values_list('UUID', flat=True))
            kwargs["guest_uuid__in"] = list(uuid_guests)
        if status != "":
            kwargs["status"] = status
        items = FormInstance.objects.filter(**kwargs)
        context={}
        context['total_items'] = items.count()
        context['items'] = items[int(page)*ITEMS_PER_PAGE:(int(page) + 1)*ITEMS_PER_PAGE]
        context['page'] = page 

        return render(request, "bookings/manage/booking-page.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def bookings_by_form(request, form_id):
    try:
        if hasattr(request, "project_id"):
            context = get_booking_context(form=get_or_none(Form, form_id), project=get_or_none(Project, request.session["project_id"]))
        else:
            context = get_booking_context(form=get_or_none(Form, form_id))
        context['total_items'] = context['items'].count()
        context['items'] = context['items'][0:ITEMS_PER_PAGE]
        context['page'] = 0
        return render (request, "bookings/manage/bookings.html", context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-bookings_by_form] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def booking_preview(request, form_uuid):
    try:
        form = get_or_none(Form, form_uuid, "uuid")
        if form == None:
            return render(request, 'error_exception.html', {'exc': _('Form not found!')})
        
        #fi = FormInstance.objects.create(form_uuid=form.uuid)
        #write_log(request.user, fi, _("Booking created"))
        
        #items = ShoppingCart.objects.filter(form_instance_id=fi.pk)
        #context = {'fi': fi, 'form': form, 'index': "0", "ro": False, 'items':items}
        context = {'form': form, 'index': "0", "ro": False,}
        return render(request, 'bookings/show-category.html', context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-new_booking] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@login_required
def test(request):
    return HttpResponse("OK")

