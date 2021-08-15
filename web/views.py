from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate
from padword.decorators import group_required
from .models import *


# Create your views here.

@group_required("admins", "projects")
def index(request):
    if hasattr(request, "project_id"):
        return redirect('bookings-by-project', request.project_id)
    return redirect('projects')
#    try:
#        return redirect('projects')
#        return render (request, "base_nestor.html")
#        #return JsonResponse({'results':serializers.serialize("json", companies, fields=('uuid','name')), 'error':0})
#    except Exception as e:
#        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})
#
'''
    Projects
'''
@group_required("admins")
def projects(request, company_id=None):
    try:
        company = get_or_none(Company, company_id)
        items = Project.objects.all() if company is None else Project.objects.filter(company = company)
        return render(request, "web/projects/projects.html", {'items':items, 'company': company})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

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
        obj = get_or_none(Project, request.GET["obj_id"]) if "obj_id" in request.GET else Project.objects.create(company=Company.objects.filter(active=1).first())
        slug = new_ui_slug(Project)
#         while Project.objects.filter(uuid=slug).exists():
#             slug = new_ui_slug()
        obj.uuid = slug

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
        obj = get_or_none(Channel, request.GET["obj_id"]) if "obj_id" in request.GET else Channel.objects.create(project=project)

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
    if obj != None:
        obj.delete()
    context = get_channels(get_or_none(Project, project_id), get_or_none(Company, company_id))
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
def get_devices(channel, project, company):
    try:
        context = {}
        if channel is not None:
            #items = Device.by_channel(channel)
            items = Device.objects.filter(channel= channel)
            context["channel"] = channel
        elif project is not None:
            #items = Device.by_project(project)
            items = project.get_devices
            context["project"] = project
        elif company is not None:
            #items = Device.by_company(company)
            projects = Projects.objects.filter(company=company)
            items = Device.objects.none()
            for project in projects:
                items = items | project.get_devices
#         uuid_list = [item.uuid for item in Project.objects.filter(company=company)]
#         items = Device.objects.filter(project_uuid__in = uuid_list)
            context["company"] = company
        else:
            items = Device.objects.all()
        print(items)
        context["items"] = items
        return context
    except Exception as e:
        print(show_exc(e))
        return {'items':Device.objects.none()}


@group_required("admins", "projects")
def devices(request, project_id = None, company_id = None, channel_id = None):
    try:
        context = get_devices(get_or_none(Channel, channel_id), get_or_none(Project, project_id), get_or_none(Company, company_id))
        return render (request, "web/devices/devices.html", context)
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@group_required("admins", "projects")
def device_search(request):
    try:
        company_id = get_param(request.GET, "company_id")
        project_id = get_param(request.GET, "project_id")
        channel_id = get_param(request.GET, "channel_id")
        company = get_or_none(Company, company_id)
        project = get_or_none(Project, project_id)
        channel = get_or_none(Channel, channel_id)
        name = get_param(request.GET, "s-name")
        filters_to_search = ["imei__icontains", "serial_number__icontains", "room__icontains", "alias__icontains"]
        items = Device.objects.none()
        for myfilter in filters_to_search:
            kwargs = {}
            if company != None:
                uuid_list = [item.uuid for item in Project.objects.filter(company=company)]
                kwargs["project_uuid__in"] = uuid_list
            if project != None:
                kwargs["project_uuid"] = project.uuid
            if channel != None:
                kwargs["channel_uuid"] = channel.uuid
            if name != "":
                kwargs[myfilter] = name
            items = items.union(Device.objects.filter(**kwargs))
        return render(request, "web/devices/device-list.html", {'items':items,'channel_id':channel_id,'project_id':project_id,'company_id':company_id,})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

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


