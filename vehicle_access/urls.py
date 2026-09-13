from django.urls import path

from . import views


app_name = "vehicle_access"

urlpatterns = [
    path("", views.vehicle_plates, name="vehicle-plates"),
    path("<int:plate_id>/remove/", views.vehicle_plate_remove, name="vehicle-plate-remove"),
]
