from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from padword.commons import show_exc, get_or_none, get_param, new_ui_slug, translate
from padword.decorators import group_required
from .models import *
from web.models import Project

# Create your views here.

@group_required("admins")
def users(request):
    try:
        items = PWUser.objects.all()
        items = sorted(items, key=lambda x: '{}_{}'.format(x.project.name, x.name))

        return render(request, 'user_remote/users/users.html', {'items':items})
    except Exception as e:
        print(show_exc(e))
        return HttpResponse(show_exc(e))

@group_required("admins")
def user_search(request):
    try:
        name = get_param(request.GET, "s-name")
        filters_to_search = ["name__icontains", "email__icontains"]
        items = Project.objects.none()

        list_uuids = Project.objects.filter(name__icontains = name).values_list('uuid', flat=True)
        items = PWUser.objects.filter(project_uuid__in = list(list_uuids))
        for myfilter in filters_to_search:
            kwargs = {}
            if name != "":
                kwargs[myfilter] = name
            items = items.union(PWUser.objects.filter(**kwargs))
        return render(request, "user_remote/users/user-row.html", {'items': items})
    except Exception as e:
        print (show_exc(e))
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

