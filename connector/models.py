from django.db import models
from django.utils.translation import ugettext as _


class ProjectAvantioUser(models.Model):
    days = models.IntegerField(verbose_name=_('Days to import'), default=1)
    username = models.CharField(max_length=255, verbose_name=_('Username'), default="")
    password = models.CharField(max_length=255, verbose_name=_('Password'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None


