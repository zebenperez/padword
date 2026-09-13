from django.contrib import admin

from .models import PlateType, VehiclePlate


@admin.register(PlateType)
class PlateTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(VehiclePlate)
class VehiclePlateAdmin(admin.ModelAdmin):
    list_display = ("plate", "plate_type", "project")
    list_filter = ("plate_type", "project")
    search_fields = ("plate", "plate_normalized", "project__name", "project__uuid")
    raw_id_fields = ("project",)
