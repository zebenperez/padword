from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from padword.commons import show_exc
import datetime

from web.models import Project

# Create your models here.

class PWUser(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="", null=True)
    name = models.CharField(max_length=255, verbose_name=_('Name'), default="", null=True)
    email = models.CharField(max_length=255, verbose_name=_('Email'), unique=True, default="", null=True)
    password = models.CharField(max_length=255, verbose_name=_('Password'), default="", null=True)
    language = models.CharField(max_length=255, verbose_name=_('Language'), default="es", null=True)
    place = models.CharField(max_length=255, verbose_name=_('Place'), default="", null=True)
    category = models.CharField(max_length=255, verbose_name=_('Category'), default="", null=True)
    checkin_notification = models.IntegerField(verbose_name=_('Checkin Notification'), default=0, null=True)
    role_id = models.IntegerField(verbose_name=_('Role Id'), default=1, null=True)
    remember_token = models.CharField(max_length=255, verbose_name=_('Remember Token'), default="", null=True)
    api_token = models.CharField(max_length=255, verbose_name=_('Api Token'), default="", null=True)
    created_at = models.DateTimeField(verbose_name=_('Created at'), default=datetime.datetime.now, null=True)
    updated_at = models.DateTimeField(verbose_name=_('Updated at'), default=datetime.datetime.now, null=True)
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="", null=True)
    #project = models.ForeignKey(Project, verbose_name = 'Project', on_delete=models.SET_NULL, null=True, to_field='uuid', db_column='project_uuid')
    available_projects = models.TextField(verbose_name=_('Available Projects'), default="", null=True)
    contacts = models.TextField(verbose_name=_('Contacts'), default="", null=True)
    available_channels = models.TextField(verbose_name=_('Available Channels'), default="", null=True)

    class Meta:
        if (len(settings.DATABASES) > 1):
            managed = False
            db_table = 'users'
        verbose_name = _('Padword Users')
        ordering = ['name']

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None
