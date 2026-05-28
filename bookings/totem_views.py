from django.contrib import auth
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _ 

from padword.decorators import group_required
from padword.commons import show_exc, get_or_none, get_param, get_float, reverse_cardkey
from web.models import Project
from bookings.models import Form
from guest.models import Guest
from guest.wristband_models import Wristband, WristbandBalance

from django.conf import settings

import datetime, time
import logging
logger = logging.getLogger(__name__)


'''
    Bookings client methods
'''
def check_user(user):
    if not user.is_authenticated:
        return False
    if not user_in_group(user, "waiters"):
        return False
    return True

def totem_access(request, project_uuid, mobile=""):
    project = get_or_none(Project, project_uuid, "uuid")

    context = {'project_uuid': project.uuid}
    if check_user(request.user):
        next_url = reverse("totem-index", kwargs = context)
    else:
        auth.logout(request)
        next_url = reverse("totem-start")

    form = Form.objects.filter(form_type__code="totem", form_type__project_uuid=project.uuid).first()
    context["next_url"] = next_url
    context["form"] = form
    context["cat"] = form.get_category
    context["mobile"] = mobile
    if mobile != "":
        request.session["mobile"] = mobile
    return render(request, 'bookings/totem/totem-welcome.html', context)

def totem_start(request):
    return render(request, "bookings/totem/totem-check-band.html", {'project_uuid': request.GET["project_uuid"], 'error': ''})

def totem_check_band(request):
    try:
        project = get_or_none(Project, request.GET["project"], "uuid")
        val = get_param(request.GET, "value", "")
        band = Wristband.get_active_by_project(project, reverse_cardkey(val))
        band_err = ""
        if band != None and band.guest != None:
            gr = band.guest.regimes.first()
            regime = gr.regime if gr != None else None
        else:
            band_err = _("This band is not asigned to any guest!")

        form = Form.get_totem(project.uuid)
        return render(request, "bookings/totem/view-band.html", {'band':band, 'band_err': band_err, 'form': form, 'project': project})
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})


#@group_required("waiters")
def totem_index(request, project_uuid):
    try:
        project = get_or_none(Project, project_uuid, "uuid")

        form = Form.get_totem(project.uuid)

        context = { 'project_uuid':project.uuid, 'form':form, }
        return render(request, "bookings/totem/index.html", context)
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

@group_required("waiters")
def totem_close(request):
    auth.logout(request)
    project_uuid = request.GET["project_uuid"] if "project_uuid" in request.GET else ""
    return redirect(reverse("totem-access", kwargs = {'project_uuid': project_uuid}))


