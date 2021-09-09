from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate
from padword.decorators import group_required
from .models import *
from guest.models import *
from web.models import Project
from bookings.models import Form

from web.models import Device
from contents.models import Category, ShoppingCart, Item
from guest.models import Guest

# from bookings.common_lib import get_or_create_form_instance, get_max_index, get_or_create_answer_instance, write_log
# from bookings.models import AnswerInstance, Field, Form, FormChannel, FormInstance, Question, Block, GuestUser

import datetime
import logging
logger = logging.getLogger(__name__)

# Create your views here.

def index(request):
    try:
        if request.user.is_authenticated:
            guest = Guest.objects.filter(email=request.user.email).first()
            categories = list(Category.objects.filter(project_uuid = guest.project.uuid).values_list('uuid', flat=True))
            forms = Form.objects.filter(category__in = categories)
            return render(request, "guest/index.html", {'forms':forms})
        else:
            return redirect(reverse('guest-form-login', kwargs={'form_uuid':'c586d361-8dce-63aa-3b8b-f1cc164a61f6'}))

    except Exception as e:
        return render(request, "error_exception.html", {'exc':show_exc(e)})
