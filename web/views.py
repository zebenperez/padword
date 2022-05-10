from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 
from django.views.decorators.csrf import csrf_exempt

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate
from padword.decorators import group_required
from .models import *


from django.conf import settings
import os



# Create your views here.

@group_required("admins", "projects", "categories", "guests")
def index(request, chk=None):
    if request.user.groups.filter(name='guests').exists():
        return redirect('pwa-index')

    if request.user.groups.filter(name='categories').exists():
        if not hasattr(request, "category_user"):
            return render(request, 'error_exception.html', {'exc': _('Category not found!')})
        #return redirect('bookings-by-category', request.category_id)
        return redirect('bookings-by-category')

    if request.user.groups.filter(name='projects').exists():
        if not hasattr(request, "project_id"):
            return render(request, 'error_exception.html', {'exc': _('Project not found!')})
        return redirect('bookings-by-project', request.project_id)

    return redirect('projects')

def thanks(request):
    return render(request, "thanks.html")

def csrf_failure(request, reason=""):
    return render(request, "csrf_error.html")

'''
    Projects
'''
@group_required("admins")
def projects(request, company_id=None, project_id=None):
    try:
        company = None
        if project_id is not None:
            project = get_or_none(Project, project_id, 'uuid')
            items = Project.objects.all() if project is None else Project.objects.filter(uuid = project.uuid)
        elif company_id is not None:
            company = get_or_none(Company, company_id)
            items = Project.objects.all() if company is None else Project.objects.filter(company = company)
        else:
            items = Project.objects.all()
        return render(request, "web/projects/projects.html", {'items':items, 'company': company})
    except Exception as e:
        print (show_exc(e))
        company = None
        items = Project.objects.all()
        return render(request, "web/projects/projects.html", {'items':items, 'company': company})

@group_required("admins")
def project_search(request):
    try:
        company_id = get_param(request.GET, "company_id")
        name = get_param(request.GET, "s-name")
        filters_to_search = ["name__icontains", "company__name__icontains"]
        items = Channel.objects.none()
        for myfilter in filters_to_search:
            kwargs = {}
            if company_id != "":
                kwargs["company__id"] = company_id
            if name != "":
                kwargs[myfilter] = name
            items = items.union(Project.objects.filter(**kwargs))
        return render(request, "web/projects/project-list.html", {'items': items, 'company_id': company_id,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins")
def project_form(request):
    try:
        obj = get_or_none(Project, request.GET["obj_id"]) if "obj_id" in request.GET else Project.objects.create(company=Company.objects.filter(active=1).first(), uuid = new_ui_slug(Project))

        company_id = get_param(request.GET, "company_id")
        if company_id != "":
            company = get_or_none(Company, company_id)
            if company != None:
                obj.company = company
                obj.save()

        return render(request, "web/projects/project-form.html", {'obj': obj, 'companies': Company.objects.all(), 'company_id': company_id})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def project_remove(request):
    company_id = get_param(request.GET, "company_id", None)
    obj = get_or_none(Project, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()

    company = get_or_none(Company, company_id)
    items = Project.objects.all() if company is None else Project.objects.filter(company = company)
    return render(request, "web/projects/project-list.html", {'items':items, 'company': company})

@group_required("admins")
def project_upload_json(request):
    obj = get_or_none(Project, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        return render(request, "web/projects/upload-json.html", {'obj':obj,})
    return render(request, 'error_exception.html', {'exc': 'Project not found!'})

'''
    Channels
'''
def get_channels(project, company):
    context = {}
    if project is not None:
        items = Channel.objects.filter(project__pk = project.id)
        context["project"] = project
    elif company is not None:
        items = Channel.objects.filter(project__company__pk = company.id)
        context["company"] = company
    else:
        items= Channel.objects.all()
    context["items"] = items
    return context

@group_required("admins", "projects")
def channels(request, project_id=None, company_id=None):
    try:
        context = get_channels(get_or_none(Project, project_id), get_or_none(Company, company_id))
        return render (request, "web/channels/channels.html", context)
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
def channel_search(request):
    try:
        company_id = get_param(request.GET, "company_id")
        project_id= get_param(request.GET, "project_id")
        name = get_param(request.GET, "s-name")
        filters_to_search = ["name__icontains", "project__name__icontains", "project__company__name__icontains"]
        items = Channel.objects.none()
        for myfilter in filters_to_search:
            kwargs = {}
            if company_id != "":
                kwargs["project__company__id"] = company_id
            if project_id != "":
                kwargs["project__id"] = project_id
            if name != "":
                kwargs[myfilter] = name
            items = items.union(Channel.objects.filter(**kwargs))
        return render(request, "web/channels/channel-list.html", {'items': items, 'project_id': project_id, 'company_id': company_id,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
def channel_form(request):
    try:
        company_id = get_param(request.GET, "company_id")
        project_id= get_param(request.GET, "project_id")
        project = get_or_none(Project, project_id)
        if project is None:
            project = Project.objects.filter(active=1).first()
        obj = get_or_none(Channel, request.GET["obj_id"]) if "obj_id" in request.GET else Channel.objects.create(project=project, uuid=new_ui_slug(Channel))

        if project_id != "":
            project = get_or_none(Project, project_id)
            if project != None:
                obj.project = project
                obj.save()

        context = {'obj': obj, 'projects': Project.objects.all(), 'project_id': project_id, 'company_id': company_id}
        return render(request, "web/channels/channel-form.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, "error_exception.html", {'exc':e})

@group_required("admins", "projects")
def channel_remove(request):
    company_id = get_param(request.GET, "company_id", None)
    project_id = get_param(request.GET, "project_id", None)
    obj = get_or_none(Channel, request.GET["obj_id"]) if "obj_id" in request.GET else None
    project = obj.project
    if obj != None:
        obj.delete()
    context = get_channels(project, get_or_none(Company, company_id))
    return render (request, "web/channels/channel-list.html", context)

'''
    Companies
'''
@group_required("admins")
def companies(request):
    try:
        items = Company.objects.all()
        return render (request, "web/companies/companies.html",{'items':items} )
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins")
def company_search(request):
    try:
        filters_to_search = ["name__icontains", ]
        items = Company.objects.none()
        for myfilter in filters_to_search:
            kwargs = {}
            if "s-name" in request.GET and request.GET["s-name"] != "":
                kwargs[myfilter] = request.GET["s-name"]
            items = items.union(Company.objects.filter(**kwargs))
        return render(request, "web/companies/company-list.html", {'items': items,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins")
def company_form(request):
    obj = get_or_none(Company, request.GET["obj_id"]) if "obj_id" in request.GET else Company.objects.create()
    return render(request, "web/companies/company-form.html", {'obj': obj,})

@group_required("admins")
def company_remove(request):
    obj = get_or_none(Company, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    items = Company.objects.all()
    return render (request, "web/companies/company-list.html",{'items':items} )

'''
    Devices
'''
#def get_devices(channel, project, company):
#    try:
#        context = {}
#        if channel is not None:
#            #items = Device.by_channel(channel)
#            items = Device.objects.filter(channel= channel)
#            context["channel"] = channel
#        elif project is not None:
#            #items = Device.by_project(project)
#            items = project.get_devices
#            context["project"] = project
#        elif company is not None:
#            #items = Device.by_company(company)
#            projects = Projects.objects.filter(company=company)
#            items = Device.objects.none()
#            for project in projects:
#                items = items | project.get_devices
##         uuid_list = [item.uuid for item in Project.objects.filter(company=company)]
##         items = Device.objects.filter(project_uuid__in = uuid_list)
#            context["company"] = company
#        else:
#            items = Device.objects.all()
#        context["items"] = items
#        return context
#    except Exception as e:
#        print(show_exc(e))
#        return {'items':Device.objects.none()}
#
#
#@group_required("admins", "projects")
#def devices(request, project_id = None, company_id = None, channel_id = None):
#    try:
#        context = get_devices(get_or_none(Channel, channel_id), get_or_none(Project, project_id), get_or_none(Company, company_id))
#        return render (request, "web/devices/devices.html", context)
#    except Exception as e:
#        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})
#
#@group_required("admins", "projects")
#def device_search(request):
#    try:
#        company_id = get_param(request.GET, "company_id")
#        project_id = get_param(request.GET, "project_id")
#        channel_id = get_param(request.GET, "channel_id")
#        company = get_or_none(Company, company_id)
#        project = get_or_none(Project, project_id)
#        channel = get_or_none(Channel, channel_id)
#        name = get_param(request.GET, "s-name")
#        filters_to_search = ["imei__icontains", "serial_number__icontains", "room__icontains", "alias__icontains"]
#        items = Device.objects.none()
#        if company != None:
#            projects = Projects.objects.filter(company=company)
#            for prj in projects:
#                items = items.union(prj.get_devices.all())
#        if project != None:
#            items = items.union(project.get_devices.all())
#        kwargs = {}
#        if channel != None:
#            kwargs["channel__uuid"] = channel.uuid
#        for myfilter in filters_to_search:
#            if name != "":
#                kwargs[myfilter] = name
#        #if kwargs:
#        items = items.union(Device.objects.filter(**kwargs))
#
#        return render(request, "web/devices/device-list.html", {'items':items,'channel_id':channel_id,'project_id':project_id,'company_id':company_id,})
#    except Exception as e:
#        print (show_exc(e))
#        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})
#
@group_required("admins", "projects")
def device_search(request):
    try:
        project = get_param(request.GET, "s-project")
        channel = get_param(request.GET, "s-channel")
        uuid = get_param(request.GET, "s-uuid")
        room = get_param(request.GET, "s-room")
        imei = get_param(request.GET, "s-imei")
        alias = get_param(request.GET, "s-alias")
        serial = get_param(request.GET, "s-serial")

        kwargs = {}
        if project != "":
            uuid_list = [item.uuid for item in Channel.objects.filter(project__name__icontains=project)]
            kwargs["channel__uuid__in"] = uuid_list
        if channel != "":
            kwargs["channel__name__icontains"] = channel
        if uuid != "":
            kwargs["uuid"] = uuid
        if imei != "":
            kwargs["room"] = room
        if imei != "":
            kwargs["imei"] = imei
        if alias != "":
            kwargs["alias__icontains"] = alias
        if serial != "":
            kwargs["serial_number"] = serial
        items = Device.objects.filter(**kwargs)

        return render(request, "web/devices/device-list.html", {'items':items,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})


@group_required("admins")
def devices(request):
    try:
        context = {'items': Device.objects.all()}
        return render (request, "web/devices/devices.html", context)
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
def devices_by_channel(request, channel_id):
    try:
        channel = get_or_none(Channel, channel_id)
        return render (request, "web/devices/devices.html", {'items': Device.by_channel(channel), 'channel_name': channel.name})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc': show_exc(e)})

@group_required("admins", "projects")
def devices_by_project(request, project_id):
    try:
        project = get_or_none(Project, project_id)
        return render (request, "web/devices/devices.html", {'items': Device.by_project(project), 'project_name': project.name})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc': show_exc(e)})

@group_required("admins", "projects")
def device_form(request):
    try:
        obj = get_or_none(Device, request.GET["obj_id"]) if "obj_id" in request.GET else Device.objects.create()

        company_id = get_param(request.GET, "company_id")
        project_id = get_param(request.GET, "project_id")
        channel_id = get_param(request.GET, "channel_id")
        if channel_id != "":
            channel = get_or_none(Channel, channel_id)
            if channel != None:
                obj.channel_uuid = channel.uuid
                obj.save()

        if project_id:
            channels = Channel.objects.filter(active=1, project=Project.objects.get(pk=project_id))
        else:
            channels = Channel.objects.filter(active=1)

        #channels = sorted(channels, key=lambda x:translate(request,x.name))
        channels = channels.all().order_by('project__company__name','project__name','name')


        context = {'obj': obj, 'channel_id': channel_id, 'project_id': project_id, 'company_id': company_id, 'channels': channels}
        return render(request, "web/devices/device-form.html", context)
    except Exception as e:
        print (show_exc(e))
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


@group_required("admins", "projects")
def device_remove(request):
    company_id = get_param(request.GET, "company_id", None)
    project_id = get_param(request.GET, "project_id", None)
    channel_id = get_param(request.GET, "channel_id", None)
    obj = get_or_none(Device, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        obj.delete()
    context = get_devices(get_or_none(Channel, channel_id), get_or_none(Project, project_id), get_or_none(Company, company_id))
    return render (request, "web/devices/device-list.html", context)


@group_required("admins", "projects")
def device_assign(request):
    try:
        device  = get_or_none(Device,  get_param(request.GET, "obj_id",     None), 'uuid')
        if device is not None and device.channel is not None:
            device.channel = None
            device.save()
            channel = get_or_none(Channel, get_param(request.GET, "channel_id", None), 'uuid')
            company = get_or_none(Company, get_param(request.GET, "company_id", None), 'uuid')
            project = get_or_none(Project, get_param(request.GET, "project_id", None), 'uuid')
            context = get_devices(channel, project, company)
            if company:
                context['company']=company
            if channel:
                context['channel']=channel
            if project:
                context['project']=project
        else:
            company = get_or_none(Company, get_param(request.GET, "company_id", None), 'uuid')
            project = get_or_none(Project, get_param(request.GET, "project_id", None), 'uuid')
            channel = get_or_none(Channel, get_param(request.GET, "channel_id", None), 'uuid')
            context = get_devices(channel, project, company)
            if channel:
                context['channel']=channel
            if project:
                context['project']=project
                if channel is None:
                    try:
                        channel = Channel.objects.get(name='DEFAULT', project= project)
                        channel.active = 1
                        channel.save()
                    except:
                        channel = Channel(uuid=new_ui_slug(Channel), name='DEFAULT', project=project, active=1)
                        channel.save()
                context['channel'] = channel
            if company:
                context['company']=company

            if channel and device:
                device.channel = channel
                device.save()

        context['noassign'] = Device.objects.filter(channel__isnull = True)
        return render (request, "web/devices/device-assign.html", context)
    except Exception as e:
        context = {}
        print(show_exc(e))
        return render (request, "web/devices/device-assign.html", context)

def check_error(request):
    return render(request, "full_error_exception.html", {'exc':"Probando mensaje de error"})

def ServiceWorker(request):
    sw_file = open(os.path.join(settings.BASE_DIR, "static", "js", "sw.js"), 'rb')
    response = HttpResponse(sw_file, content_type='application/javascript')
    return response
#     template_name = "sw.js"
#     content_type="application/javascript"
