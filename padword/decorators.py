from django.shortcuts import render, redirect
from web.models import ProjectUser, Project
from contents.models import CategoryUser

def group_required(*group_names):
    def _method_wrapper(f):
        def _arguments_wrapper(request, *args, **kwargs) :
            if request.user.is_authenticated:
                if bool(request.user.groups.filter(name__in=group_names)) or request.user.is_superuser:
                    cu = CategoryUser.objects.filter(username=request.user.username).first()
                    if cu != None:
                        request.category_user = cu
                        #request.category_id = cu.category.id
                    pu = ProjectUser.objects.filter(username=request.user.username).first()
                    if pu != None and pu.project != None:
                        request.project_id = pu.project.id
                    return f(request, *args, **kwargs)
                #else:
                #	return (render(request, "generic/error_exception.html", {'exc':"This user have not permission to access to this section"}))
            return redirect('auth_login')
        return _arguments_wrapper
    return _method_wrapper

