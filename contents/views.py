from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import *
from django.core import serializers
from padword.commons import show_exc, get_or_none, get_param

# Create your views here.

@login_required
def index(request):
    try:
        categories = Category.objects.all()
        return JsonResponse({'results':len(categories), 'error':0})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def categories_by_project(request, project_id):
    try:
        project = Project.objects.get(uuid=project_id)
        categories = Category.objects.filter(project_uuid=project_id, parent_uuid__isnull =True, is_active=1).order_by('pk')
        return render(request, "contents/categories.html", {'project':project, 'items':categories})
        return JsonResponse({'results':len(categories), 'error':0})
    except Exception as e:
        return JsonResponse({'results':[], 'error':1, 'error-msg':show_exc(e)})

@login_required
def category_form(request):
    obj = get_or_none(Category, request.GET["obj_id"]) if "obj_id" in request.GET else Category.objects.create()
    project_id = get_param(request.GET, "project_id")
    if project_id != "":
        project = get_or_none(Project, project_id)
        if project != None:
            obj.project = project
            obj.save()

    return render(request, "contents/category-form.html", {'obj': obj, 'company_id': company_id})
