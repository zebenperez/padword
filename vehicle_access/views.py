from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from padword.decorators import group_required
from web.models import Project

from .forms import VehiclePlateForm
from .models import VehiclePlate


@group_required("projects")
def vehicle_plates(request):
    project = get_object_or_404(Project, id=request.project_id)

    if request.method == "POST":
        form = VehiclePlateForm(request.POST, project=project)
        if form.is_valid():
            vehicle_plate = form.save(commit=False)
            vehicle_plate.project = project
            vehicle_plate.save()
            messages.success(request, "Matrícula registrada correctamente.")
            return redirect("vehicle_access:vehicle-plates")
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
        },
    )


@group_required("projects")
def vehicle_plate_remove(request, plate_id):
    if request.method != "POST":
        return redirect("vehicle_access:vehicle-plates")

    project = get_object_or_404(Project, id=request.project_id)
    vehicle_plate = get_object_or_404(VehiclePlate, id=plate_id, project=project)
    vehicle_plate.delete()
    messages.success(request, "Matrícula eliminada correctamente.")
    return redirect("vehicle_access:vehicle-plates")
