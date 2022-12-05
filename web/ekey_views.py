from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc, get_or_none
from padword.decorators import group_required
from .models import *


'''
    eKeys
'''
@group_required("admins")
def ekeys_by_project(request, project_id):
    try:
        project = get_or_none(Project, project_id)
        return render (request, "web/ekeys/ekeys.html", {'project': project, 'ekey_list': project.ekey_list()})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

