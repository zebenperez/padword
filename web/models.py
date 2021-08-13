from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext as _
from padword.commons import show_exc
import datetime

# Create your models here.

class Company(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="", null=True)
    name = models.CharField(max_length=255, verbose_name=_('Name'), default="", null=True)
    active = models.IntegerField(verbose_name=_('Active'), default=1, null=True)
    created_at = models.DateTimeField(verbose_name=_('Created at'), default=datetime.datetime.now, null=True)
    class Meta:
        if (len(settings.DATABASES) > 1):
            managed = False
            db_table = 'companies'
        verbose_name = _('Company')
        ordering = ['name']

class Project(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    name = models.CharField(max_length=255, verbose_name=_('Name'), default="")
    longitude = models.CharField(max_length=255, verbose_name=_('Longitude'), default="", blank=True)
    latitude = models.CharField(max_length=255, verbose_name=_('Latitude'), default="", blank=True)
    default_language = models.CharField(max_length=255, verbose_name=_('Default languaje'), default="ES", blank=True)
    currency = models.CharField(max_length=255, verbose_name=_('Currency'), default="EUR", blank=True)
    radius = models.IntegerField(verbose_name=_('Radius (Km)'), default=100)
    active = models.IntegerField(verbose_name=_('Active'), default=1)
    created_at = models.DateTimeField(verbose_name=_('Created at'), default=datetime.datetime.now)

    company = models.ForeignKey(Company, verbose_name=_('Company'), on_delete=models.SET_NULL, null=True)

    class Meta:
        if (len(settings.DATABASES) > 1):
            managed = False
            db_table = 'projects'
        verbose_name = _('Project')
        ordering = ['company__name', 'name']

    def __str__(self):
        return self.name

    @property
    def get_devices(self):
        try:
            devices = Device.objects.filter(channel__in = Channel.objects.filter(project=self))
            return devices
        except Exception as e:
            print(show_exc(e))
            return Device.objects.none()

    @property
    def devices_number(self):
        devices = Device.objects.filter(channel__in = Channel.objects.filter(project=self))
        return devices.count()

class Channel(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="", unique=True)
    ui_uuid = models.CharField(max_length=255, verbose_name=_('UI-UUID'), default='00000000-0000-0000-0000-000000000000')
    name = models.CharField(max_length=255, verbose_name=_('Name'), default="")
    active = models.IntegerField(verbose_name=_('Active'), default=1)
    created_at = models.DateTimeField(verbose_name=_('Created at'), default=datetime.datetime.now)

    project = models.ForeignKey(Project, verbose_name=_('Project'), on_delete=models.SET_NULL, null=True)

    class Meta:
        if (len(settings.DATABASES) > 1):
            managed = False
            db_table = 'channels'
        verbose_name = _('Channel')
        ordering = ['project__name', 'name']

class ProjectUser(models.Model):
    #channels = models.ManyToManyField(Channel, verbose_name=_("Channels"), blank=True)
    project = models.ForeignKey(Project, verbose_name=_('Project'), on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, verbose_name=_('User'), on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name = _('Project user')

class Device(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    alias = models.CharField(max_length=255, verbose_name=_('Alias'), default="", null=True)
    imei = models.CharField(max_length=255, verbose_name=_('IMEI'), default="", null=True)
    net_type = models.CharField(max_length=255, verbose_name=_('Net type'), default="", null=True)
    mac = models.CharField(max_length=255, verbose_name=_('Mac'), null=False, default='00:00:00:00:00:00')
    wifi_mac = models.CharField(max_length=255, verbose_name=_('WiFi Mac'), null=False, default='00:00:00:00:00:00')
    room = models.CharField(max_length=255, verbose_name=_('Room'), default="")
    android_id_padword = models.CharField(max_length=255, verbose_name=_('Android ID'), default="")
    serial_number = models.CharField(max_length=255, verbose_name=_('Serial Number'), default="")
    active = models.IntegerField(verbose_name=_('Active'), default=1)
    created_at = models.DateTimeField(verbose_name=_('Created at'), default=datetime.datetime.now)
    #channel_id = models.CharField(max_length=255, verbose_name='Channel ID', default="")

    channel = models.ForeignKey(Channel, verbose_name=_('Channel'), on_delete=models.SET_NULL, null=True, to_field='uuid')

    class Meta:
        if (len(settings.DATABASES) > 1):
            managed = False
            db_table = 'devices'
        verbose_name = _('Device')
        ordering = ['imei']

    @property
    def project(self):
        try:
            return (Channel.objects.get(uuid=self.channel_id).project)
        except Exception as e:
            return (Project(uuid='0000-0000-00000000', name='UNDEFINED'))

    @property
    def project_uuid(self):
        try:
            print (1)
            return (Channel.objects.get(uuid=self.channel_id).project.uuid)
        except Exception as e:
            return ('0000-0000-00000000')

    @classmethod
    def by_project(cls, projects):
        try:
            items = Device.objects.none()
            for project in projects:
                items = items.union(Device.objects.filter(channel__project__uuid = project.uuid))
            return (items)
        except Exception as e:
            print (show_exc(e))
            return (Device.objects.none())

    @classmethod
    def by_company(cls, companies):
        try:
            items = Device.objects.none()
            for company in companies:
                projects = Project.objects.filter(company__pk = company.pk)
                items = items.union(Device.objects.filter(project_uuid__in = projects.all().values_list('uuid', flat=True)))
            return (items)
        except Exception as e:
            print (show_exc(e))
            return (Device.objects.none())

    @classmethod
    def by_channel(cls, channels):
        try:
            items = Device.objects.none()
            for channel in channels:
                items = items.union(Device.objects.filter(channel_id = channel.uuid))
            return (items)
        except Exception as e:
            print (show_exc(e))
            return (Device.objects.none())

class DeviceByProject(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    alias = models.CharField(max_length=255, verbose_name=_('Alias'), default="", null=True)
    imei = models.CharField(max_length=255, verbose_name=_('IMEI'), default="", null=True)
    net_type = models.CharField(max_length=255, verbose_name=_('Net type'), default="", null=True)
    mac = models.CharField(max_length=255, verbose_name=_('Mac'), null=False, default='00:00:00:00:00:00')
    wifi_mac = models.CharField(max_length=255, verbose_name=_('WiFi Mac'), null=False, default='00:00:00:00:00:00')
    room = models.CharField(max_length=255, verbose_name=_('Room'), default="")
    android_id_padword = models.CharField(max_length=255, verbose_name=_('Android ID'), default="")
    serial_number = models.CharField(max_length=255, verbose_name=_('Serial Number'), default="")
    active = models.IntegerField(verbose_name=_('Active'), default=1)
    created_at = models.DateTimeField(verbose_name=_('Created at'), default=datetime.datetime.now)
    channel_id = models.CharField(max_length=255, verbose_name=_('Channel ID'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    #channel = models.ForeignKey(Channel, verbose_name = 'Channel', on_delete=models.SET_NULL, null=True)

    class Meta:
        if (len(settings.DATABASES) > 1):
            managed = False
            db_table = '`devices-by-projects`'
        verbose_name = _('Device')
        ordering = ['imei']

    @property
    def channel(self):
        try:
            return (Channel.objects.get(uuid=self.channel_id))
        except Exception as e:
            return (Channel(uuid='0000-0000-00000000', name='UNDEFINED'))

    @property
    def project(self):
        try:
            return (Channel.objects.get(uuid=self.channel_id).project)
        except Exception as e:
            return (Project(uuid='0000-0000-00000000', name='UNDEFINED'))

    @classmethod
    def by_project(cls, projects):
        try:
            items = Device.objects.none()
            for project in projects:
                items = items.union(Device.objects.filter(project_uuid = project.uuid))
            return (items)
        except Exception as e:
            print (show_exc(e))
            return (Device.objects.none())

    @classmethod
    def by_company(cls, companies):
        try:
            items = Device.objects.none()
            for company in companies:
                projects = Project.objects.filter(company__pk = company.pk)
                items = items.union(Device.objects.filter(project_uuid__in = projects.all().values_list('uuid', flat=True)))
            return (items)
        except Exception as e:
            print (show_exc(e))
            return (Device.objects.none())

    @classmethod
    def by_channel(cls, channels):
        try:
            items = Device.objects.none()
            for channel in channels:
                items = items.union(Device.objects.filter(channel_id = channel.uuid))
            return (items)
        except Exception as e:
            print (show_exc(e))
            return (Device.objects.none())
