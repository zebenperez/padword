from django.urls import path

from . import views


app_name = "vehicle_access"

urlpatterns = [
    path("", views.vehicle_plates, name="vehicle-plates"),
    path("<int:plate_id>/remove/", views.vehicle_plate_remove, name="vehicle-plate-remove"),
    path("admin/", views.admin_projects, name="admin-projects"),
    path("admin/search/", views.admin_projects_search, name="admin-projects-search"),
    path("admin/<slug:project_uuid>/", views.admin_vehicle_plates, name="admin-vehicle-plates"),
    path(
        "admin/<slug:project_uuid>/<int:plate_id>/remove/",
        views.admin_vehicle_plate_remove,
        name="admin-vehicle-plate-remove",
    ),
]
