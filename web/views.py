from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 
from django.views.decorators.csrf import csrf_exempt

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate, set_session, update_cron, get_int, translate2, get_random_str
from padword.decorators import group_required
from guest.models import Regime, ProjectRegime, GuestType, Wristband, Guest, GuestStripe
from guest.models import WristbandAccessZone, WristbandAccessZoneTimes, WristbandAccessPoint
from sensibo.models import ProjectSensiboUser
from connector.models import ProjectAvantioUser, ProjectAvaibookUser, ProjectWinhotelUser, ProjectStripeUser
from connector.models import ProjectMewsUser, ProjectCarUser
from contents.models import Category, PointOfSale, PointOfSaleCategory, Table
from bookings.models import Form, FormInstance
from .models import *
#from .lock_lib import ShLock


from django.conf import settings
import os, re, requests, time, datetime, csv



@group_required("admins", "projects", "categories", "guests")
def index(request, chk=None):
    if request.user.groups.filter(name='guests').exists():
        return redirect('pwa-index')

    if request.user.groups.filter(name='categories').exists():
        if not hasattr(request, "category_user"):
            return render(request, 'error_exception.html', {'exc': _('Category not found!')})
        #return redirect('bookings-by-category', request.category_id)
        #return redirect('bookings-by-category')
        return redirect('categories-by-categories')

    if request.user.groups.filter(name='projects').exists():
        if not hasattr(request, "project_id"):
            return render(request, 'error_exception.html', {'exc': _('Project not found!')})
        #return redirect('bookings-by-project', request.project_id)
        return redirect_project_user(request)

    return redirect('projects')

def redirect_project_user(request):
    project = get_or_none(Project, request.project_id)
    if project == None:
        return render(request, 'error_exception.html', {'exc': _('Project not found!')})

    menu = project.get_first_menu(request.user.username)
    try:
        return redirect(menu.url)
        #return redirect(menu.url)
    except:
        #return render(request, 'error_exception.html', {'exc': _('Menu not found!')})
        if menu == "orders":
            return redirect('bookings-by-project')
            #return redirect('bookings-by-project', request.project_id)
        elif menu == "guests":
            #return redirect('guests-by-project', project.uuid)
            return redirect('guests-by-project')
        elif menu == "notifications":
            return redirect('guest-notifications')
        elif menu == "rooms":
            return redirect('rooms-by-project')
        elif menu == "locks":
            return redirect('locks-by-project2')
            #return redirect('locks-by-project2', request.project_id)
        else:
            return render(request, 'error_exception.html', {'exc': _('Menu not found!')})

def thanks(request):
    return render(request, "thanks.html")

def csrf_failure(request, reason=""):
    return render(request, "csrf_error.html")

def get_or_create_user_lock(project_uuid):
    obj, created = ProjectLockUser.objects.get_or_create(project_uuid = project_uuid)
    return obj 

def get_or_create_user_sensibo(project_uuid):
    obj, created = ProjectSensiboUser.objects.get_or_create(project_uuid = project_uuid)
    return obj 

def get_or_create_user_avantio(project_uuid):
    obj, created = ProjectAvantioUser.objects.get_or_create(project_uuid = project_uuid)
    return obj 

def get_or_create_user_avaibook(project_uuid):
    obj, created = ProjectAvaibookUser.objects.get_or_create(project_uuid = project_uuid)
    return obj 

def get_or_create_user_winhotel(project_uuid):
    obj, created = ProjectWinhotelUser.objects.get_or_create(project_uuid = project_uuid)
    return obj 

def get_or_create_user_stripe(project_uuid):
    obj, created = ProjectStripeUser.objects.get_or_create(project_uuid = project_uuid)
    return obj 

def get_or_create_user_mews(project_uuid):
    obj, created = ProjectMewsUser.objects.get_or_create(project_uuid = project_uuid)
    return obj 

def get_or_create_user_cars(project_uuid):
    obj, created = ProjectCarUser.objects.get_or_create(project_uuid = project_uuid)
    return obj 

'''
    Projects
'''
@group_required("admins", "projects", "categories", "guests")
def set_project(request, uuid=None):
    request.session["project"] = uuid 
    return redirect(index)

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
        return render(request, "web/projects/projects.html", {'items':items, 'company': company, 'active': 'projects'})
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

        user_lock = get_or_create_user_lock(obj.uuid)
        user_sensibo = get_or_create_user_sensibo(obj.uuid)
        user_avantio = get_or_create_user_avantio(obj.uuid)
        user_avaibook = get_or_create_user_avaibook(obj.uuid)
        user_winhotel = get_or_create_user_winhotel(obj.uuid)
        user_stripe = get_or_create_user_stripe(obj.uuid)
        user_mews = get_or_create_user_mews(obj.uuid)
        user_cars = get_or_create_user_cars(obj.uuid)

        regime_list = Regime.objects.all()
        point_of_sale_list = PointOfSale.objects.filter(project_uuid=obj.uuid)
        #table_list = Table.objects.filter(project_uuid=obj.uuid)
        form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=obj.uuid).first()
        context = {
            'obj': obj, 
            'companies': Company.objects.all(), 
            'company_id': company_id, 
            'user_lock': user_lock, 
            'user_sensibo': user_sensibo, 
            'user_avantio': user_avantio, 
            'user_avaibook': user_avaibook, 
            'user_winhotel': user_winhotel, 
            'user_stripe': user_stripe, 
            'user_mews': user_mews, 
            'user_cars': user_cars, 
            'project_regime_list': [item.regime for item in obj.regimes.all()],
            'regime_list': regime_list,
            'point_of_sale_list': point_of_sale_list,
            #'table_list': table_list,
            'form': form
        }
        return render(request, "web/projects/project-form.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins")
def project_details(request, obj_id, current_tab=""):
    try:
        obj = get_or_none(Project, obj_id) 

        user_lock = get_or_create_user_lock(obj.uuid)
        user_sensibo = get_or_create_user_sensibo(obj.uuid)
        user_avantio = get_or_create_user_avantio(obj.uuid)
        user_avaibook = get_or_create_user_avaibook(obj.uuid)
        user_winhotel = get_or_create_user_winhotel(obj.uuid)
        user_stripe = get_or_create_user_stripe(obj.uuid)
        user_mews = get_or_create_user_mews(obj.uuid)
        user_cars = get_or_create_user_cars(obj.uuid)

        regime_list = Regime.objects.all()
        point_of_sale_list = PointOfSale.objects.filter(project_uuid=obj.uuid)
        invitation_list = Invitation.objects.filter(project_uuid=obj.uuid)
        guest_type_list = GuestType.objects.filter(project_uuid=obj.uuid)
        access_zones = WristbandAccessZone.objects.filter(project_uuid=obj.uuid)
        #access_list = WristbandAccessPoint.objects.filter(project_uuid=obj.uuid)
        form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=obj.uuid).first()
        context = {
            'obj': obj, 
            'companies': Company.objects.all(), 
            'user_lock': user_lock, 
            'user_sensibo': user_sensibo, 
            'user_avantio': user_avantio, 
            'user_avaibook': user_avaibook, 
            'user_winhotel': user_winhotel, 
            'user_stripe': user_stripe, 
            'user_mews': user_mews, 
            'user_cars': user_cars, 
            'project_regime_list': [item.regime for item in obj.regimes.all()],
            'regime_list': regime_list,
            'point_of_sale_list': point_of_sale_list,
            'invitation_list': invitation_list,
            'guest_type_list': guest_type_list,
            'access_zones': access_zones,
            'current_tab': current_tab,
            'form': form
        }
        return render(request, "web/projects/project-details.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


@group_required("admins")
def project_remove(request):
    company_id = get_param(request.GET, "company_id", None)
    obj = get_or_none(Project, request.GET["obj_id"]) if "obj_id" in request.GET else None
    if obj != None:
        ProjectLockUser.objects.filter(project_uuid=obj.uuid).delete()
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

@group_required("admins")
def project_user_token(request):
    obj = get_or_none(ProjectLockUser, request.GET["obj_id"]) if "obj_id" in request.GET else None
    obj.get_token()

    return render(request, "web/projects/project-token.html", {'user_lock':obj,})

@group_required("admins")
def project_user_refresh_token(request):
    obj = get_or_none(ProjectLockUser, request.GET["obj_id"]) if "obj_id" in request.GET else None
    obj.get_new_token()

    return render(request, "web/projects/project-token.html", {'user_lock':obj,})

@group_required("admins")
def project_regime_toggle(request):
    try:
        project = get_or_none(Project, request.GET["project_id"])
        regime = get_or_none(Regime, request.GET["obj_id"])
        pr_list = ProjectRegime.objects.filter(regime=regime, project=project)
        if len(pr_list) > 0:
            pr_list.delete()
        else:
            ProjectRegime.objects.create(regime=regime, project=project)
    except Exception as e:
        print (show_exc(e))
    return HttpResponse("")

@group_required("admins")
def project_pos_add(request):
    try:
        project = get_or_none(Project, request.GET["obj_id"])
        PointOfSale.objects.create(project_uuid=project.uuid, uuid=new_ui_slug(PointOfSale))
        point_of_sale_list = PointOfSale.objects.filter(project_uuid=project.uuid)
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-point-of-sales-list.html", {'point_of_sale_list':point_of_sale_list,})

@group_required("admins")
def project_pos_remove(request):
    try:
        pos = get_or_none(PointOfSale, request.GET["obj_id"])
        project = get_or_none(Project, pos.project_uuid, "uuid")
        pos.delete()
        point_of_sale_list = PointOfSale.objects.filter(project_uuid=project.uuid)
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-point-of-sales-list.html", {'point_of_sale_list':point_of_sale_list,})

@group_required("admins")
def project_pos_cat_toggle(request):
    try:
        pos = get_or_none(PointOfSale, request.GET["obj_id"])
        cat = get_or_none(Category, request.GET["category_id"])
        item_list = PointOfSaleCategory.objects.filter(point_of_sale=pos, category=cat)
        if len(item_list) > 0:
            item_list.delete()
        else:
            PointOfSaleCategory.objects.create(point_of_sale=pos, category=cat)
    except Exception as e:
        print (show_exc(e))
    return HttpResponse("")

@group_required("admins", "projects", "categories")
def project_pos_add_image(request):
    try:
        obj_id = request.POST["obj_id"]
        image = request.FILES["file"]

        item = get_or_none(PointOfSale, obj_id)
        if item != None:
            item.image = image
            item.save()
        return render(request, "web/projects/pos-img.html", {"obj": item,})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects", "categories")
def project_pos_remove_image(request):
    try:
        obj_id = request.GET["obj_id"]
        obj = get_or_none(PointOfSale, obj_id) 
        obj.image.delete(save=True)

        return render(request, "web/projects/pos-img.html", {"obj": obj,})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects", "categories")
def project_pos_daily_summary(request, obj_id):
    try:
        obj = get_or_none(PointOfSale, obj_id) 
        today = datetime.datetime.today()
        today_str = today.strftime("%Y-%m-%d")

        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}_{}.csv"'.format(today_str, obj.name)},
        )

        writer = csv.writer(response)
        writer.writerow(['_TPV', '_TPVNom', '_Rate', 'ProductUId', '_Description', 'Date', 'Tiket_UID', '_Price', '_Units', '_Discount', 'TotalPrice', '_Room', '_ClientId'])

        #s_date = datetime.datetime.strptime("{} 00:00".format(today_str), "%Y-%m-%d %H:%M")
        s_date = datetime.datetime.strptime("2023-11-01 00:00".format(today_str), "%Y-%m-%d %H:%M")
        e_date = datetime.datetime.strptime("{} 23:59:59".format(today_str), "%Y-%m-%d %H:%M:%S")
        fi_list = FormInstance.objects.filter(pos_uuid=obj.uuid, date__range=(s_date, e_date))
        for fi in fi_list:
            info = fi.info.first()
            room = info.client_room if info != None else ""
            client_id = info.client_id if info != None else ""
            for item in fi.get_items:
                code = obj.name[:4].upper()
                name = obj.name
                desc = translate2("es", item.name) 
                date = fi.date.strftime("%Y%m%d%H%M")
                discount = (item.low_price/item.price)*100 if item.low_price < item.price else 0
                total_price = item.low_price if item.low_price < item.price else item.price
                writer.writerow([code, name, "", item.id, desc, date, fi.id, item.price, 1, discount, total_price, room, client_id])
        return response
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins")
def project_table_add(request):
    table_list = []
    try:
        pos = get_or_none(PointOfSale, request.GET["obj_id"])
        Table.objects.create(point_of_sale=pos, uuid=new_ui_slug(Table))
        table_list = Table.objects.filter(pos_uuid=pos.uuid)
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-table-list.html", {'item': pos, 'table_list': table_list,})

@group_required("admins")
def project_table_remove(request):
    try:
        table = get_or_none(Table, request.GET["obj_id"])
        pos = table.point_of_sale
        table.delete()
        table_list = Table.objects.filter(point_of_sale = pos)
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-table-list.html", {'item': pos, 'table_list': table_list,})

@group_required("admins")
def project_table_range(request):
    try:
        pos = get_or_none(PointOfSale, request.POST["pos_id"])
        ini = get_int(request.POST["ini"])
        end = get_int(request.POST["end"]) + 1

        for i in range(ini, end):
            name = "{} {}".format(get_param(request.POST, "name"), i)
            Table.objects.create(point_of_sale=pos, uuid=new_ui_slug(Table), name=name)

        table_list = Table.objects.filter(point_of_sale = pos)
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-table-list.html", {'item': pos, 'table_list': table_list,})

@group_required("admins")
def project_set_avantio_schedule(request):
    try:
        pau = get_or_none(ProjectAvantioUser, request.GET["obj_id"])
        val = get_param(request.GET, "value")
        field = get_param(request.GET, "field")
        if pau != None:
            if field == "hour":
                pau.hour = val
            elif field == "minute":
                pau.minute = val
            elif field == "hour_notif":
                pau.hour_notif = val
            pau.save()

            function = ""
            if field == "hour" or field == "minute": 
                function = "avantio_booking_schedule"
                hour = pau.hour
                minute = pau.minute
            elif field == "hour_notif":
                function = "avantio_notification_schedule"
                hour = "\*\|{}".format(pau.hour_notif)
                minute = "0"
            if function != "":
                update_cron(hour, minute, function, pau.project_uuid)

        return HttpResponse("Saved!")
    except Exception as e:
        print (show_exc(e))
        return HttpResponse("Error!")

@group_required("admins")
def project_set_winhotel_schedule(request):
    try:
        pau = get_or_none(ProjectWinhotelUser, request.GET["obj_id"])
        val = get_param(request.GET, "value")
        field = get_param(request.GET, "field")
        if pau != None:
            if field == "hour":
                pau.hour = val
            elif field == "minute":
                pau.minute = val
            elif field == "hour_price":
                pau.hour_price = val
            elif field == "hour_cancel":
                pau.hour_cancel = val
            pau.save()

            function = ""
            if field == "hour": 
                function = "winhotel_booking_schedule"
                hour = "\*\|{}".format(pau.hour)
                minute = "0"
            elif field == "minute":
                function = "winhotel_check_schedule"
                hour = "%"
                minute = "\*\|{}".format(pau.minute)
            if field == "hour_price": 
                function = "winhotel_price_schedule"
                hour = "\*\|{}".format(pau.hour_price)
                minute = "0"
            if field == "hour_cancel": 
                function = "winhotel_cancel_schedule"
                hour = "\*\|{}".format(pau.hour_cancel)
                minute = "0"
            if function != "":
                update_cron(hour, minute, function, pau.project_uuid)

        return HttpResponse("Saved!")
    except Exception as e:
        print (show_exc(e))
        return HttpResponse("Error!")

@group_required("admins")
def project_set_lock_schedule(request):
    try:
        user_lock = get_or_none(ProjectLockUser, get_param(request.GET, "obj_id"))
        project_uuid = get_param(request.GET, "project_uuid")
        time = get_param(request.GET, "time")

        user_lock.time_schedule_tasks = time
        user_lock.save()

        function = "locks_tasks_schedule"
        
        hour = time.split(":")[0] if time != "-1" else time
        minute = time.split(":")[1] if time != "-1" else time
        update_cron(hour.lstrip("0"), minute.lstrip("0"), function, project_uuid)
        return HttpResponse("Saved!")
    except Exception as e:
        print (show_exc(e))
        return HttpResponse("Error!")

@group_required("admins")
def project_set_mews_schedule(request):
    try:
        pau = get_or_none(ProjectMewsUser, request.GET["obj_id"])
        val = get_param(request.GET, "value")
        field = get_param(request.GET, "field")
        if pau != None:
            if field == "hour":
                pau.hour = val
            elif field == "minute":
                pau.minute = val
            pau.save()

            function = ""
            if field == "hour" or field == "minute": 
                function = "mews_booking_schedule"
                hour = pau.hour
                minute = pau.minute
            if function != "":
                update_cron(hour, minute, function, pau.project_uuid)

        return HttpResponse("Saved!")
    except Exception as e:
        print (show_exc(e))
        return HttpResponse("Error!")

@group_required("admins")
def project_add_logo(request):
    try:
        project = get_or_none(Project, request.POST["obj_id"])
        logo = request.FILES["file"]

        if project != None:
            project.logo = logo
            project.save()
        return render(request, "web/projects/project-img.html", {"obj": project,})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins", "projects", "categories")
def project_remove_logo(request):
    try:
        obj = get_or_none(Project, request.GET["obj_id"]) 
        obj.logo.delete(save=True)
        return render(request, "web/projects/project-img.html", {"obj": obj,})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

@group_required("admins")
def project_invitation_add(request):
    try:
        project = get_or_none(Project, request.GET["obj_id"])
        Invitation.objects.create(project_uuid=project.uuid, uuid=new_ui_slug(Invitation))
        invitation_list = Invitation.objects.filter(project_uuid=project.uuid)
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-invitation-list.html", {'invitation_list':invitation_list,})

@group_required("admins")
def project_invitation_remove(request):
    try:
        inv = get_or_none(Invitation, request.GET["obj_id"])
        project = get_or_none(Project, inv.project_uuid, "uuid")
        inv.delete()
        invitation_list = Invitation.objects.filter(project_uuid=project.uuid)
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-invitation-list.html", {'invitation_list':invitation_list,})

@group_required("admins")
def project_guest_types_add(request):
    try:
        project = get_or_none(Project, request.GET["obj_id"])
        GuestType.objects.create(project_uuid=project.uuid, uuid=new_ui_slug(GuestType))
        guest_type_list = GuestType.objects.filter(project_uuid=project.uuid)
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-guest-types-list.html", {'guest_type_list':guest_type_list,})

@group_required("admins")
def project_guest_types_remove(request):
    try:
        gtype = get_or_none(GuestType, request.GET["obj_id"])
        project = get_or_none(Project, inv.project_uuid, "uuid")
        gtype.delete()
        guest_type_list = GuestType.objects.filter(project_uuid=project.uuid)
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-guest-types-list.html", {'guest_type_list':guest_type_list,})

@group_required("admins")
def project_access_zone_add(request):
    try:
        project = get_or_none(Project, request.GET["obj_id"])
        WristbandAccessZone.objects.create(project_uuid=project.uuid, uuid=new_ui_slug(WristbandAccessZone))
        access_zones = WristbandAccessZone.objects.filter(project_uuid=project.uuid)
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-access-zones-list.html", {'obj': project, 'access_zones':access_zones,})

@group_required("admins")
def project_access_zone_remove(request):
    try:
        zone = get_or_none(WristbandAccessZone, request.GET["obj_id"])
        #project = get_or_none(Project, zone.project_uuid, "uuid")
        project_uuid = zone.project_uuid
        for point in zone.accesspoints.all():
            point.delete()
        for times in zone.timetable.all():
            times.delete()
        zone.delete()
        access_zones = WristbandAccessZone.objects.filter(project_uuid=project_uuid)
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-access-zones-list.html", {'access_zones':access_zones,})

@group_required("admins")
def project_access_zone_close(request):
    try:
        zone = get_or_none(WristbandAccessZone, request.GET["obj_id"])
        close = get_param(request.GET, "close")
        project_uuid = zone.project_uuid
        for point in zone.accesspoints.all():
            point.close = True if close == "True" else False
            point.save()
        access_zones = WristbandAccessZone.objects.filter(project_uuid=project_uuid)
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-access-zones-list.html", {'access_zones':access_zones,})

@group_required("admins")
def project_access_points_add(request):
    try:
        zone = get_or_none(WristbandAccessZone, request.GET["obj_id"])
        WristbandAccessPoint.objects.create(zone=zone, uuid=new_ui_slug(WristbandAccessPoint))
        access_list = zone.accesspoints.all()
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-access-points-list.html", {'access_list':access_list,})

@group_required("admins")
def project_access_points_remove(request):
    try:
        access = get_or_none(WristbandAccessPoint, request.GET["obj_id"])
        zone = access.zone
        access.delete()
        access_list = zone.accesspoints.all()
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-access-points-list.html", {'access_list':access_list,})

@group_required("admins")
def project_access_zone_times_add(request):
    try:
        zone = get_or_none(WristbandAccessZone, request.GET["obj_id"])
        WristbandAccessZoneTimes.objects.create(zone=zone)
        access_times = zone.timetable.all()
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-access-zone-times-list.html", {'access_times':access_times,})

@group_required("admins")
def project_access_zone_times_remove(request):
    try:
        access = get_or_none(WristbandAccessZoneTimes, request.GET["obj_id"])
        zone = access.zone
        access.delete()
        access_times = zone.timetable.all()
    except Exception as e:
        print (show_exc(e))
    return render(request, "web/projects/project-form-access-zone-times-list.html", {'access_times':access_times,})



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
        return render (request, "web/companies/companies.html",{'items':items, 'active': 'companies'} )
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
        context = {'items': Device.objects.all(), 'active': 'devices'}
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

'''
    Modules
'''
@group_required("admins", "projects")
def show_module(request):
    try:
        module = Module.objects.filter(code=request.GET["code"]).first()
        return render (request, "show-module.html", {'module': module})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc': show_exc(e)})


'''
    Logs
'''
@group_required("admins")
def logs(request):
    current_log = os.path.join(settings.BASE_DIR, "logs.txt")
    f = open(current_log, "r", encoding='utf-8')
    size = os.path.getsize(current_log)
    text = ""
    if size < 1000:
        text = f.read()
    else:
        i = 0
        for line in f.readlines():
            if i > 1000:
                break
            text += line 
            i += 1
    try:
        #log_list = os.listdir(settings.LOGPATH)
        log_list = [f for f in os.listdir(settings.LOGPATH) if re.match(r'.*logs.*', f)]
    except:
        log_list = []
    return render(request, 'logs.html', {'text': text.replace("\n", "<br/>"), 'log_list': log_list, 'current_log': current_log})

from django.http import FileResponse

@group_required("admins")
def download_log(request):
    try:    
        name = request.GET["name"]
        response = FileResponse(open(os.path.join(settings.LOGPATH, name), 'rb'))
        return response
    except Exception as e:
        return render(request, 'error_exception.html', {'exc': show_exc(e)})

#REMOVE
@group_required("admins")
def get_menus(request):
    try:
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename=menus.csv"'},
        )
        
        writer = csv.writer(response)
        writer.writerow(['pu_id', 'menu_id'])

        item_list = ProjectUser.objects.all()
        for item in item_list:
            for m in item.menus_mod.all():
                writer.writerow([item.id, m.id])
        return response
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'msg': str(e)})

#REMOVE
@group_required("admins")
def set_menus(request):
    f = open("static/menus.csv", "r", encoding='utf-8')
    i = 0
    for line in f.readlines():
        l = line.split(",")
        pu = get_or_none(ProjectUser, l[0])
        m = get_or_none(Menu, l[1].replace("\n", ""))
        if pu != None and m != None:
            pum, created = ProjectUserMenu.objects.get_or_create(project_user=pu, menu=m)
            if created:
                pum.order = i
                pum.save()
            print(pu.username)
            print(m)
        print(i)
        i = i + 1
    return HttpResponse("OK")


#'''
#    Locks
#'''
#def update_locks():
#    sh_lock = ShLock()
#    for item in sh_lock.get_locks():
#        Lock.objects.get_or_create(uuid=item)
#
##def set_lock_filter_session(request):
##    request.session["lock_search_alias"] = request.GET["s-alias"] if "s-alias" in request.GET and request.GET["s-alias"] else ""
#
#def get_lock_items(request):
#    kwargs = {}
#
#    if "lock_search_alias" in request.session and request.session["lock_search_alias"] != "":
#        kwargs["alias__icontains"] = request.session["lock_search_alias"]
#    if "lock_search_project" in request.session and request.session["lock_search_project"] != "":
#        project_uuid_list = [item.uuid for item in Project.objects.filter(name__icontains=request.session["lock_search_project"])]
#        kwargs["project_uuid__in"] = project_uuid_list
#
#    return Lock.objects.filter(**kwargs) if len(kwargs) > 0 else Lock.objects.all()
#
#@group_required("admins")
#def locks(request):
#    msg = ""
#    try:
#        update_locks()
#    except Exception as e:
#        msg = e
# 
#    try:
#        items = get_lock_items(request)
#        return render (request, "web/locks/locks.html",{'items':items, 'msg': msg})
#    except Exception as e:
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})
#
#@group_required("admins")
#def lock_search(request):
#    try:
#        #set_lock_filter_session(request)
#        set_session(request, "lock_search_alias")
#        set_session(request, "lock_search_project")
#        items = get_lock_items(request)
#        return render(request, "web/locks/lock-list.html", {'items': items,})
#    except Exception as e:
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})
#
#@group_required("admins")
#def lock_form(request):
#    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
#    if obj == None:
#        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
#    return render(request, "web/locks/lock-form.html", {'obj': obj,})
#
#@group_required("admins")
#def lock_remove(request):
#    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
#    if obj != None:
#        obj.delete()
#    items = Lock.objects.all()
#    return render (request, "web/locks/lock-list.html",{'items':items} )
#
#@group_required("admins")
#def lock_get_all_passcodes(request, obj_id=None):
#    obj = get_or_none(Lock, request.GET["obj_id"]) if "obj_id" in request.GET else None
#    if obj == None:
#        return render(request, 'error_exception.html', {'exc':'Lock not found!'})
#    return render(request, "web/locks/lock-all-passcodes.html", {'obj': obj,})
#
#@group_required("admins")
#def lock_set_code(request):
#    try:
#        code = request.POST["code"]
#        card = request.POST["card"]
#        print("--1--")
#        print(code)
#        print(card)
#        for key in request.POST.keys():
#            if "ch_" in key:
#                print(key)
#                print(request.POST[key])
#                print("-----------------")
#        return redirect(locks)
#    except Exception as e:
#        return render(request, 'error_exception.html', {'exc':show_exc(e)})
#
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
#
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

#from .libstripe import *
#@group_required("admins")
#def stripe_alta_client(reqeuest, uuid_guest):
#    # test_client_uuid = a57efd6c-02e3-0d16-50fe-8c45d760bb8f
#    try:
#        guest = Guest.objects.get(UUID=uuid_guest)
#    except Exception as e:
#        print (show_exc(e))
#        guest = None
#    if guest is None:
#        return HttpResponse("Guest not found!")
#    else:
#        email = guest.UUID + "@padword.es"  # Email ficticio, para identificar al cliente
#        name = f'{guest.name} {guest.surname}'
#
#        API_KEY = "sk_test_51PAwwh14EEiK5wo0fArBnn5kkPbri8PkDCTyiqcC2jknwqwYqjjSwHP8NQQmtVESzuIJ95TPukiN5m509SptMRAN00mmKFNDkW"
#        customer_data = {
#            "email": email,
#            "name": name,
#        }
#        obj_id = create_stripe_customer(API_KEY, customer_data)
#        session = stripe.checkout.Session.create(
#            customer = obj_id,
#            line_items=[{
#                'price_data': {
#                    'currency': 'eur',
#                    'product_data': {
#                        'name': 'Precarga',
#                    },
#                    'unit_amount': 100,
#                },
#                'quantity': 1,
#            }],
#            mode='payment', 
#            payment_method_options = {'card': {'setup_future_usage': 'off_session'}},
#            success_url='https://padword.shidix.es/web/stripe/store-payment/{CHECKOUT_SESSION_ID}',
#            cancel_url=f'https://padword.shidix.es/guest/guests/details/{guest.pk}/',
#        )
#        return redirect(session.url, code=303)

#@group_required("admins")
#def stripe_store_payment(request, session_id):
#    try:
#        API_KEY = "sk_test_51PAwwh14EEiK5wo0fArBnn5kkPbri8PkDCTyiqcC2jknwqwYqjjSwHP8NQQmtVESzuIJ95TPukiN5m509SptMRAN00mmKFNDkW"
#        session = stripe.checkout.Session.retrieve(session_id)
#        payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent)
#        customer = stripe.Customer.retrieve(session.customer)
#        email = customer.email
#        guest = Guest.objects.get(UUID=email.split("@")[0])
#        if payment_intent.status == "succeeded":
#            try:
#                guest_stripe = GuestStripe.objects.get(guest=guest)
#            except:
#                guest_stripe = GuestStripe(guest=guest)
#            guest_stripe.stripe_id = session.customer
#            guest_stripe.payment_method = payment_intent.payment_method
#            guest_stripe.save()
#
#
#            return redirect(reverse('guest-details', kwargs={'obj_id': guest.pk}))
#        else:
#            return HttpResponse("Payment KO")
#    except Exception as e:
#        print (show_exc(e))
#        return HttpResponse("Error")

#@csrf_exempt
#def stripe_payment(request):
#    # wristband code = 4038674227
#    try:
#        if request.method == "POST":
#            key_value = request.POST["key_value"]
#            if key_value != "cH4Va?9qZSM_cFM!Kdo-hhmvENfqluOMbjxH-lDCMjhleaqCrCB?my8jMYl-?u!!JevHI2InZF!PFHXzZht_1Qkkxagaj?UPYuAvk3pEp-7LoDLPmUV9xRefYSedY!ba":
#                return HttpResponse("Error")
#            wristband_code = request.POST["wb_code"]
#            amount = request.POST["amount"]
#            wristband = Wristband.objects.get(code=wristband_code)
#            guest = wristband.guest
#            guest_stripe = GuestStripe.objects.get(guest=guest)
#            API_KEY = "sk_test_51PAwwh14EEiK5wo0fArBnn5kkPbri8PkDCTyiqcC2jknwqwYqjjSwHP8NQQmtVESzuIJ95TPukiN5m509SptMRAN00mmKFNDkW"
#            obj_id = create_stripe_payment_intent(API_KEY, guest_stripe.stripe_id, guest_stripe.payment_method, int(amount), "123", "eur")
#            if obj_id != "":
#                return HttpResponse("OK")
#            else:
#                return HttpResponse("Error")
#        else:
#            return HttpResponse("Error")
#    except Exception as e:
#        print (show_exc(e))
#        return HttpResponse("Error")
#
#@group_required("admins")
#def stripe_error_payment(request):
#    return HttpResponse("Error")

#@group_required("admins")
#def stripe_test_payment(request, test_type=-1):
#    #import stripe
#
#    API_KEY = "sk_test_51PAwwh14EEiK5wo0fArBnn5kkPbri8PkDCTyiqcC2jknwqwYqjjSwHP8NQQmtVESzuIJ95TPukiN5m509SptMRAN00mmKFNDkW"
#    payment_method_data = {
#            # "type": "card",
#            "card": {
#                "number": "4242424242424242",
#                "exp_month": 12,
#                "exp_year": 2029,
#                "cvc": "123",
#            }
#        }
#
#    if type(test_type) == str:
#        print (test_type)
#        session = stripe.checkout.Session.retrieve(test_type)
#        return HttpResponse(f'{session}<hr>')
#
#    elif test_type == -1:
#        print (test_type)
#        return HttpResponse("OK")
#    elif test_type == 0:
#        import random
#        obj_id = create_stripe_payment_intent(API_KEY, "cus_Q9LsDjy8eXJZX6", "pm_1PJ3GL14EEiK5wo03ZnybHBz", int(random.randint(1,100000)), "123", "eur")
#
#    elif test_type == 1:
#
#        customer_data = {
#            "email": "none@shidix.com",
#            "name": "Shidix",
#            "description": "Shidix Customer",
#            "phone": "123456789",
#            "address": {
#                "city": "Finca España",
#                "country": "ES",
#                "line1": "Avenida Las Palmeras",
#                "line2": "19",
#                "postal_code": "38230",
#                "state": "Santa Cruz de Tenerife"
#            }
#        }
#        obj_id = create_stripe_customer(API_KEY, customer_data)
#    elif test_type == 2:
#        customer_data = {
#            "email": "none@shidix.com",
#            "name": "Shidix",
#        }
#        obj_id = create_stripe_customer(API_KEY, customer_data)
#        intents = stripe.PaymentIntent.list(customer=obj_id, limit=1)
#        for intent in intents:
#            break
#        import random
#        obj_id = create_stripe_payment_intent(API_KEY, obj_id, intent.payment_method, random.randint(1,100000), "123", "eur")
#
#
#    elif test_type == 4:
#        stripe.api_key = API_KEY
#        customer_data = {
#            "email": "none@shidix.com",
#            "name": "Shidix",
#        }
#        obj_id = create_stripe_customer(API_KEY, customer_data)
#
#        session = stripe.checkout.Session.create(
#            customer = obj_id,
#            line_items=[{
#                'price_data': {
#                    'currency': 'eur',
#                    'product_data': {
#                        'name': 'Precarga',
#                    },
#                    'unit_amount': 100,
#                },
#                'quantity': 1,
#            }],
#            mode='payment', 
#            payment_method_options = {'card': {'setup_future_usage': 'off_session'}},
#            success_url='https://padword.shidix.es/web/stripe/test-payment/{CHECKOUT_SESSION_ID}',
#            cancel_url='https://padword.shidix.es/web/stripe/test-payment/',
#        )
#        return redirect(session.url, code=303)
#
#    return HttpResponse(f'{obj_id}<hr>')
