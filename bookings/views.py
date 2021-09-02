from django.http import HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, get_bool, new_ui_slug
from web.models import Channel, Project, ProjectUser
from contents.models import Category, ShoppingCart, Item
from user_remote.models import PWUser

from .common_lib import write_log
from .models import Form, FormInstance, Status

import datetime
import logging
logger = logging.getLogger(__name__)


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
    if remote_user == "":
        return render(request, 'error_exception.html', {'exc': _('User not found!')})
    
#    try:
#        user = User.objects.get(username=remote_user.email)
#    except:
#        try:
#            projects_group = Group.objects.get(name='projects') 
#            user = User.objects.create_user(remote_user.email, email=remote_user.email)
#            projects_group.user_set.add(user)
#        except:
#            return render(request, 'error_exception.html', {'exc': _('Group not found!')})
#
#    pu, created = ProjectUser.objects.get_or_create(project_uuid=project_uuid, username=user.username)

    user = ProjectUser.get_or_create_project_user(project_uuid, remote_user.email)
    auth.login(request, user)
    return redirect(bookings_by_project, project.id)

'''
    Bookings
'''
def get_booking_context(form=None, project=None):
    context = {}
    today = datetime.datetime.today()

    kwargs = {'date__year': today.year, 'date__month': today.month, 'date__day': today.day}
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
        context["msg"] = 'No hay resultados para la búsqueda. Presentamos las últimas 100 reservas'
        items = FormInstance.objects.all()[:100]

    context["ini_date"] = today
    context["end_date"] = today
    context["status_list"] = Status.objects.all()
    context["items"] = items
    return context

@group_required("admins")
def bookings(request):
    try:
        context = get_booking_context()
        return render (request, "bookings/bookings.html", context)
    except Exception as e:
        logger.error("[bookings-bookings] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def bookings_by_form(request, form_id):
    try:
        if hasattr(request, "project_id"):
            context = get_booking_context(form=get_or_none(Form, form_id), project=get_or_none(Project, request.session["project_id"]))
        else:
            context = get_booking_context(form=get_or_none(Form, form_id))
        return render (request, "bookings/bookings.html", context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-bookings_by_form] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def bookings_by_project(request, project_id):
    try:
        context = get_booking_context(project=get_or_none(Project, project_id))
        return render (request, "bookings/bookings.html", context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-bookings_by_project] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})
    return render(request, 'error_exception.html', {'exc':'Unknown error'})

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
            kwargs["date__lte"] = end_date
        if name != "":
            kwargs["name__icontains"] = name
        if status != "":
            kwargs["status"] = status
        items = FormInstance.objects.filter(**kwargs)

        return render(request, "bookings/booking-list.html", {'items':items,})
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def booking_preview(request, form_uuid):
    try:
        form = get_or_none(Form, form_uuid, "uuid")
        if form == None:
            return render(request, 'error_exception.html', {'exc': _('Form not found!')})
        
        fi = FormInstance.objects.create(form_uuid=form.uuid)
        write_log(request.user, fi, _("Booking created"))
        
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk)
        context = {'fi': fi, 'index': "0", "ro": False, 'items':items}
        return render(request, 'bookings/fillform.html', context)
    except Exception as e:
        print (show_exc(e))
        logger.error("[bookings-new_booking] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


@group_required("admins", "projects")
def booking_view(request, fi_id):
    try:
        fi = FormInstance.objects.get(pk = fi_id)
        form = get_or_none(Form, fi.form_uuid, 'uuid')
        items = ShoppingCart.objects.filter(form_instance_id=fi.pk)
        if fi.status != None and fi.status.code == "01":
            previous_status = fi.status.name
            fi.set_status("02")
            write_log(request.user, fi, _("Status change from {} to {}".format(previous_status, fi.status.name)))
        context = {'fi': fi, 'index': "0", "ro": True, 'items':items}
        return render(request, 'bookings/fillform.html', context)
    except Exception as e:
        print(e)
        logger.error("[bookings-fill_form] {}".format(str(e)))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def change_status(request):
    try:
        if request.POST:
            status = get_or_none(Status, request.POST["status"])
            fi = FormInstance.objects.get(pk = request.POST["fi_id"])
            previous_status = fi.status.name if fi.status != None else "Created"
            fi.set_status(status.code)
            write_log(request.user, fi, _("Status change from {} to {}".format(previous_status, fi.status.name)))
            return redirect(bookings_by_form, fi.form.id)
    except Exception as e:
        print(e)
        logger.error("[bookings-change_status] {}".format(str(e)))
    return render(request, 'error_exception.html', {})

@group_required("admins", "projects")
def status_form(request):
    try:
        obj = get_or_none(FormInstance, request.GET["obj_id"]) if "obj_id" in request.GET else FormInstance.objects.create()
        return render(request, "bookings/status-form.html", {'obj': obj, 'status_list': Status.objects.all()})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def booking_log(request, fi_id):
    try:
        fi = get_or_none(FormInstance, fi_id)
        return render(request, 'bookings/booking-logs.html', {'fi': fi})
    except Exception as e:
        logger.error("[bookings-new_booking] {}".format(str(e)))
    return render(request, 'error_exception.html', {})


@login_required
def test(request):
    form_id = request.GET["form_id"]
    return HttpResponse(form_id)

