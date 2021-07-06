from django.db import models
from django.utils.translation import ugettext as _
from padword.commons import show_exc

from web.models import Channel, Project

# Create your models here.

class Guest(models.Model):
#     channel = models.ForeignKey('web.Channel', to_field='uuid', on_delete=models.SET_NULL, null=True)
#     project = models.ForeignKey('web.Project', to_field='uuid', on_delete=models.SET_NULL, null=True)
    PID = models.IntegerField(verbose_name='PID')
    room = models.CharField(max_length=255, verbose_name='Room')
    name = models.CharField(max_length=255, verbose_name='Name')
    surname = models.CharField(max_length=255, verbose_name='Surname')
    project_id = models.CharField(max_length=255, verbose_name='Project')
    channel_id = models.CharField(max_length=255, verbose_name='Channel')
    language = models.CharField(max_length=255, verbose_name='Language')
    check_in = models.DateTimeField(verbose_name='Check-In')
    check_out = models.DateTimeField(verbose_name='Check-Out')

    @property
    def project(self):
        try:
            return Project.objects.get(uuid = self.project_id)
        except Exception as e:
            return Project(name='UNKNOWN')

    @property
    def channel(self):
        try:
            return Channel.objects.get(uuid = self.channel_id)
        except Exception as e:
            return Channel(name='UNKNOWN')

    @classmethod
    def by_project(cls, projects):
        try:
            items = Guest.objects.none()
            if isinstance(projects, models.query.QuerySet):
                for project_uuid in projects.all().values_list('uuid', flat=True):
                    items = items.union(Guest.objects.filter(project_id = project_uuid))
            else:
                items = Guest.objects.filter(project_id = projects.uuid)
            return items
        except Exception as e:
            print (show_exc(e))
            return Guest.objects.none()

    @classmethod
    def by_channel(cls, channels):
        try:
            items = Guest.objects.none()
            if isinstance(channels, models.query.QuerySet):
                for channel_uuid in channels.all().values_list('uuid', flat=True):
                    items = items.union(Guest.objects.filter(channel_id = channel_uuid))
            else:
                items = Guest.objects.filter(channel_id = channels.uuid)
            return items
        except Exception as e:
            print (show_exc(e))
            return Guest.objects.none()
        

    class Meta:
        managed = False
        db_table = 'guests-by-channel'
        verbose_name = _('Guest')

