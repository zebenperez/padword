from django.db import models
from django.utils.translation import ugettext as _
from padword.commons import show_exc
from django.conf import settings

from web.models import Channel, Project

import datetime

class Guest(models.Model):
#     channel = models.ForeignKey('web.Channel', to_field='uuid', on_delete=models.SET_NULL, null=True)
#     project = models.ForeignKey('web.Project', to_field='uuid', on_delete=models.SET_NULL, null=True)
    PID = models.IntegerField(verbose_name='PID', default=0)
    UUID = models.CharField(max_length=255, verbose_name='UUID', default="")
    room = models.CharField(max_length=255, verbose_name='Room', default="")
    name = models.CharField(max_length=255, verbose_name='Name', default="")
    surname = models.CharField(max_length=255, verbose_name='Surname', default="")
    referral = models.CharField(max_length=255, verbose_name='Referral', default="")
    guest_type = models.CharField(max_length=255, verbose_name='Guest Type', default="guest")
    project_id = models.CharField(max_length=255, verbose_name='Project', default="")
    language = models.CharField(max_length=255, verbose_name='Language', default="")
    birthdate = models.DateField(verbose_name='Birthdate', default=datetime.date.today)
    check_in = models.DateTimeField(verbose_name='Check-In', default=datetime.datetime.now)
    check_out = models.DateTimeField(verbose_name='Check-Out', default=datetime.datetime.now)
    language = models.CharField(max_length=255, verbose_name='Language', default="es")
    country = models.CharField(max_length=255, verbose_name='Country', default="es")
    pin = models.CharField(max_length=255, verbose_name='PIN', default="0000000")
    married = models.IntegerField(verbose_name='Married', default=0)
    with_kids = models.IntegerField(verbose_name='With kids', default=0)
    adults = models.IntegerField(verbose_name='Adults', default=0)
    children = models.IntegerField(verbose_name='Childrens', default=0)
    babies = models.IntegerField(verbose_name='Babies', default=0)
    mobile = models.CharField(max_length=255, verbose_name='Mobile', default="")
    email = models.CharField(max_length=255, verbose_name='Email', default="")
    balance = models.FloatField(verbose_name='Balance', default=0.)
    deleted = models.IntegerField(verbose_name='Deleted', default=0)

    @property
    def project(self):
        try:
            return Project.objects.get(uuid = self.project_id)
        except Exception as e:
            return Project(name='UNKNOWN')

    @property
    def channels(self):
        try:
            channels_uuid = GuestByChannel.objects.filter(UUID = self.UUID).values_list('channel_id', flat=True)
            items = Channel.objects.none()
            for uuid in channels_uuid:
                items = items.union(Channel.objects.filter(uuid=uuid))
            return (items)
        except Exception as e:
            print (show_exc(e))
            return Channel.objects.none()

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
            items = GuestByChannel.objects.none()
            if isinstance(channels, models.query.QuerySet):
                for channel_uuid in channels.all().values_list('uuid', flat=True):
                    items = items.union(GuestByChannel.objects.filter(channel_id = channel_uuid))
            else:
                items = GuestByChannel.objects.filter(channel_id = channels.uuid)
            items = Guest.objects.filter(UUID__in = items.all().values_list('UUID', flat=True))
            return items
        except Exception as e:
            print (show_exc(e))
            return Guest.objects.none()
       
    @staticmethod
    def current_by_room_project(room, project):
        date = datetime.datetime.now()
        return Guest.objects.filter(room=room, project_id=project, check_in__lte=date, check_out__gte=date)

    class Meta:
        if len (settings.DATABASES) > 1:
            managed = False
            db_table = 'guests'
        verbose_name = _('Guest')

class GuestByChannel(models.Model):
#     channel = models.ForeignKey('web.Channel', to_field='uuid', on_delete=models.SET_NULL, null=True)
#     project = models.ForeignKey('web.Project', to_field='uuid', on_delete=models.SET_NULL, null=True)
    PID = models.IntegerField(verbose_name='PID')
    UUID = models.CharField(max_length=255, verbose_name='UUID')
    room = models.CharField(max_length=255, verbose_name='Room')
    name = models.CharField(max_length=255, verbose_name='Name')
    surname = models.CharField(max_length=255, verbose_name='Surname')
    project_id = models.CharField(max_length=255, verbose_name='Project')
    channel_id = models.CharField(max_length=255, verbose_name='Channel')
    language = models.CharField(max_length=255, verbose_name='Language')
    check_in = models.DateTimeField(verbose_name='Check-In')
    check_out = models.DateTimeField(verbose_name='Check-Out')
    referral = models.CharField(max_length=255, verbose_name='Referral', default="")
    guest_type = models.CharField(max_length=255, verbose_name='Guest Type', default="guest")
    birthdate = models.DateField(verbose_name='Birthdate', default=datetime.date.today)
    country = models.CharField(max_length=255, verbose_name='Country', default="es")
    pin = models.CharField(max_length=255, verbose_name='PIN', default="0000000")
    married = models.IntegerField(verbose_name='Married', default=0)
    with_kids = models.IntegerField(verbose_name='With kids', default=0)
    adults = models.IntegerField(verbose_name='Adults', default=0)
    children = models.IntegerField(verbose_name='Childrens', default=0)
    babies = models.IntegerField(verbose_name='Babies', default=0)
    mobile = models.CharField(max_length=255, verbose_name='Mobile', default="")
    email = models.CharField(max_length=255, verbose_name='Email', default="")
    balance = models.FloatField(verbose_name='Balance', default=0.)
    deleted = models.IntegerField(verbose_name='Deleted', default=0)

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
        if len (settings.DATABASES) > 1:
            managed = False
            db_table = 'guests-by-channel'
        verbose_name = _('Guest')
