from django.shortcuts import render, redirect
from django.urls import resolve
from web.models import ProjectUser, Project, Waiter
from contents.models import CategoryUser

import logging
logger = logging.getLogger(__name__)


def group_required(*group_names):
    def _method_wrapper(f):
        def _arguments_wrapper(request, *args, **kwargs) :
            logger.info("[{}]: \"{}\"".format(request.user, request.path_info))
            if request.user.is_authenticated:
                if bool(request.user.groups.filter(name__in=group_names)) or request.user.is_superuser:
                    cu = CategoryUser.objects.filter(username=request.user.username).first()
                    if cu != None:
                        request.category_user = cu
                        #request.category_id = cu.category.id

                    pu = None
                    if "project" in request.session and request.session["project"] != "":
                        pu = ProjectUser.objects.filter(project_uuid=request.session["project"], username=request.user.username).first()
                    if pu == None:
                        pu = ProjectUser.objects.filter(username=request.user.username).first()
                    if pu != None and pu.project != None:
                        request.project_id = pu.project.id
                        if "project" not in request.session or request.session["project"] == "":
                            request.session["project"] = pu.project.uuid

                    waiter = Waiter.objects.filter(username=request.user.username).first()
                    if waiter != None:
                        request.waiter = waiter
                    return f(request, *args, **kwargs)
                #else:
                #	return (render(request, "generic/error_exception.html", {'exc':"This user have not permission to access to this section"}))
            return redirect('auth_login')
        return _arguments_wrapper
    return _method_wrapper

