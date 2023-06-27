from django.db import models
from django.utils.translation import ugettext as _


class ProjectAvantioUser(models.Model):
    days = models.IntegerField(verbose_name=_('Days to import'), default=1)
    hour = models.IntegerField(verbose_name=_('Hour to import'), default=0)
    minute = models.IntegerField(verbose_name=_('Minutes to import'), default=0)
    hour_notif = models.IntegerField(verbose_name=_('Hour to import notifications'), default=0)
    username = models.CharField(max_length=255, verbose_name=_('Username'), default="")
    password = models.CharField(max_length=255, verbose_name=_('Password'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None


