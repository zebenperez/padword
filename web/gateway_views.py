from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate, set_session, reverse_cardkey
from padword.decorators import group_required
from .models import *
from .lock_lib import ShLock
from guest.models import KeyCode, KeyCard

import requests
import time, datetime, pytz


'''
    Gateway
'''
@group_required("admins")
def gateways_by_project(request, project_id):
    try:
        project = get_or_none(Project, project_id)
        return render (request, "web/gateways/gateways.html", {'project': project, 'gateway_list': project.gateway_list()})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

'''
    Gateway for "projects" users
'''
@group_required("projects")
def gateways_by_project2(request):
    try:
        project = get_or_none(Project, request.project_id)
        context = {'project': project, 'gateway_list': project.gateway_list(), 'active': 'gateways'}
        return render (request, "web/gateways-by-project/gateways.html", context)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

