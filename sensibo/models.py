from django.db import models
from django.utils.translation import ugettext as _


class ProjectSensiboUser(models.Model):
    api_key = models.CharField(max_length=255, verbose_name=_('API KEY'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

class SensiboDevice(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    name = models.CharField(max_length=255, verbose_name=_('Name'), default="")
    room = models.CharField(max_length=255, verbose_name=_('Room'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except Exception as e:
            return None

