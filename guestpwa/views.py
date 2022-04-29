from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse
from padword.commons import show_exc, get_or_none

from bookings.models import Form, FormInstance
from bookings.common_lib import get_guest
from contents.models import Category, ItemPromo
from guest.models import Guest
#from web.models import Project

import datetime

import logging
logger = logging.getLogger(__name__)


#DEPRECATED???
def index(request, project_uuid=None):
    try:
        if request.user.is_authenticated:
            guest = Guest.objects.filter(email=request.user.email).first()
            categories = list(Category.objects.filter(project_uuid = guest.project.uuid).values_list('uuid', flat=True))
            forms = Form.objects.filter(category__in = categories, active=True)
            return render(request, "guest/index.html", {'forms':forms, 'project_uuid':guest.project.uuid})
        else:
            return redirect(reverse('guest-access-bookings', kwargs={'project_uuid':project_uuid}))
    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})

def index_cat(request, category_uuid=None):
    try:
        if request.user.is_authenticated:
            cat_uuid = request.GET["category_uuid"] if category_uuid == None else category_uuid
            cat = get_or_none(Category, cat_uuid, "uuid")
            form = Form.objects.filter(category = cat_uuid).first()
            context = {'category': cat, 'form': form, 'project_uuid': cat.project.uuid}
            return render(request, "bookings/show-category-pwa.html", context)
        else:
            return redirect(reverse('guest-access-bookings', kwargs={'project_uuid':project_uuid}))
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

def get_promos(request):
    try:
        now = datetime.datetime.now()
        promo_list = ItemPromo.objects.filter(ini_date__lte=now, end_date__gte=now)
        #promos = []
        promo = None
        for p in promo_list:
            if p.item.project.uuid == request.GET["project_uuid"]:
                #promos.append(promo)
                promo = p
                break
        return render(request, "guest/show-promo.html", {'item': promo.item}) if promo != None else HttpResponse("")
    except Exception as e:
        print(e)
        return render(request, "error_exception.html", {'exc':show_exc(e)})

