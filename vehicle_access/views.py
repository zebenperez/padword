from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from padword.commons import get_param
from padword.decorators import group_required
from web.models import Project

from .forms import VehiclePlateForm
from .models import VehiclePlate


def _recent_projects(request):
    project_uuids = request.session.get("vehicle_access_recent_projects", [])
    projects_by_uuid = {
        project.uuid: project
        for project in Project.objects.filter(uuid__in=project_uuids).select_related("company")
    }
    return [projects_by_uuid[uuid] for uuid in project_uuids if uuid in projects_by_uuid]


def _remember_project(request, project_uuid):
    project_uuids = request.session.get("vehicle_access_recent_projects", [])
    project_uuids = [uuid for uuid in project_uuids if uuid != project_uuid]
    request.session["vehicle_access_recent_projects"] = [project_uuid] + project_uuids[:4]


def _vehicle_plates(request, project, list_url, admin_mode=False):

    if request.method == "POST":
        form = VehiclePlateForm(request.POST, project=project)
        if form.is_valid():
            vehicle_plate = form.save(commit=False)
            vehicle_plate.project = project
            vehicle_plate.save()
            messages.success(request, "Matrícula registrada correctamente.")
            return redirect(list_url, project_uuid=project.uuid) if admin_mode else redirect(list_url)
    else:
        form = VehiclePlateForm(project=project)

    vehicle_plate_list = VehiclePlate.objects.filter(project=project).select_related(
        "plate_type"
    )
    return render(
        request,
        "vehicle_access/vehicle_plate_list.html",
        {
            "active": "vehicle-access",
            "form": form,
            "has_plate_types": form.fields["plate_type"].queryset.exists(),
            "project": project,
            "vehicle_plate_list": vehicle_plate_list,
            "admin_mode": admin_mode,
        },
    )


@group_required("projects", "admins")
def vehicle_plates(request):
    if request.user.is_superuser or request.user.groups.filter(name="admins").exists():
        return redirect("vehicle_access:admin-projects")
    project = get_object_or_404(Project, id=request.project_id)
    return _vehicle_plates(request, project, "vehicle_access:vehicle-plates")


def _vehicle_plate_remove(request, project, plate_id, list_url, admin_mode=False):
    if request.method != "POST":
        return redirect(list_url, project_uuid=project.uuid) if admin_mode else redirect(list_url)

    vehicle_plate = get_object_or_404(VehiclePlate, id=plate_id, project=project)
    vehicle_plate.delete()
    messages.success(request, "Matrícula eliminada correctamente.")
    return redirect(list_url, project_uuid=project.uuid) if admin_mode else redirect(list_url)


@group_required("projects")
def vehicle_plate_remove(request, plate_id):
    project = get_object_or_404(Project, id=request.project_id)
    return _vehicle_plate_remove(request, project, plate_id, "vehicle_access:vehicle-plates")


@group_required("admins")
def admin_projects(request):
    return render(request, "vehicle_access/admin_projects.html", {
        "projects": _recent_projects(request),
        "active": "vehicle-access",
    })


@group_required("admins")
def admin_projects_search(request):
    name = get_param(request.GET, "project_search_name").strip()
    projects = Project.objects.filter(name__icontains=name).select_related("company")[:15] if len(name) >= 3 else []
    return render(request, "vehicle_access/admin_projects_list.html", {
        "projects": projects,
        "searching": True,
        "minimum_characters": len(name) < 3,
    })


@group_required("admins")
def admin_vehicle_plates(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    _remember_project(request, project.uuid)
    return _vehicle_plates(
        request,
        project,
        "vehicle_access:admin-vehicle-plates",
        admin_mode=True,
    )


@group_required("admins")
def admin_vehicle_plate_remove(request, project_uuid, plate_id):
    project = get_object_or_404(Project, uuid=project_uuid)
    return _vehicle_plate_remove(
        request,
        project,
        plate_id,
        "vehicle_access:admin-vehicle-plates",
        admin_mode=True,
    )
