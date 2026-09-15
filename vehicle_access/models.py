import re

from django.db import models
from django.utils.translation import ugettext_lazy as _


def normalize_plate(value):
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


class PlateType(models.Model):
    name = models.CharField(_("Nombre"), max_length=100, unique=True)

    class Meta:
        verbose_name = _("Tipo de matrícula")
        verbose_name_plural = _("Tipos de matrícula")
        ordering = ["name"]

    def __str__(self):
        return self.name


class VehiclePlate(models.Model):
    plate = models.CharField(_("Matrícula"), max_length=20)
    plate_normalized = models.CharField(
        _("Matrícula normalizada"), max_length=20, editable=False
    )
    plate_type = models.ForeignKey(
        PlateType,
        verbose_name=_("Tipo de matrícula"),
        on_delete=models.PROTECT,
        related_name="vehicle_plates",
    )
    project = models.ForeignKey(
        "web.Project",
        verbose_name=_("Proyecto"),
        to_field="uuid",
        db_column="project_uuid",
        on_delete=models.CASCADE,
        related_name="vehicle_plates",
    )

    class Meta:
        verbose_name = _("Matrícula de vehículo")
        verbose_name_plural = _("Matrículas de vehículos")
        ordering = ["project", "plate_normalized"]
        #constraints = [
        #    models.UniqueConstraint(
        #        fields=["project", "plate_normalized"],
        #        name="vehicle_access_unique_plate_project",
        #    )
        #]

    def __str__(self):
        return self.plate

    def save(self, *args, **kwargs):
        self.plate_normalized = normalize_plate(self.plate)
        super().save(*args, **kwargs)
