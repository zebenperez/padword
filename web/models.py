from django.db import models
from django.utils.translation import ugettext as _
from padword.commons import show_exc

# Create your models here.

class Company(models.Model):
    uuid = models.CharField(max_length=255, verbose_name='UUID')
    name = models.CharField(max_length=255, verbose_name='Name')
    active = models.IntegerField(verbose_name = 'Active')
    created_at = models.DateTimeField(verbose_name='Created at')
    class Meta:
        managed = False
        db_table = 'companies'
        verbose_name = _('Company')
        ordering = ['name']

class Project(models.Model):
    uuid = models.CharField(max_length=255, verbose_name='UUID')
    name = models.CharField(max_length=255, verbose_name='Name')
    active = models.IntegerField(verbose_name = 'Active')
    company = models.ForeignKey(Company, verbose_name = 'Company', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(verbose_name='Created at')
    class Meta:
        managed = False
        db_table = 'projects'
        verbose_name = _('Project')
        ordering = ['company__name', 'name']

    @property
    def get_devices(self):
        #devices = Device.objects.filter(channel_id__in = Channel.objects.filter(project=self))
        devices = Device.objects.filter(project_uuid = self.uuid)
        return devices

class Channel(models.Model):
    uuid = models.CharField(max_length=255, verbose_name='UUID')
    ui_uuid = models.CharField(max_length=255, verbose_name='UI-UUID', default='00000000-0000-0000-0000-000000000000')
    name = models.CharField(max_length=255, verbose_name='Name')
    active = models.IntegerField(verbose_name = 'Active')
    project = models.ForeignKey(Project, verbose_name = 'Project', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(verbose_name='Created at')
    class Meta:
        managed = False
        db_table = 'channels'
        verbose_name = _('Channel')
        ordering = ['project__name', 'name']

class Device(models.Model):
    uuid = models.CharField(max_length=255, verbose_name='UUID')
    alias = models.CharField(max_length=255, verbose_name='Alias', null=True)
    imei = models.CharField(max_length=255, verbose_name='IMEI', null=True)
    net_type = models.CharField(max_length=255, verbose_name='Tipo de red', null=True)
    mac = models.CharField(max_length=255, verbose_name='Mac', null=False, default='00:00:00:00:00:00')
    wifi_mac = models.CharField(max_length=255, verbose_name='WiFi Mac', null=False, default='00:00:00:00:00:00')
    channel_id = models.CharField(max_length=255, verbose_name='Channel ID')
    room = models.CharField(max_length=255, verbose_name='Room')
    android_id_padword = models.CharField(max_length=255, verbose_name='Android ID')
    serial_number = models.CharField(max_length=255, verbose_name='Serial Number')
    active = models.IntegerField(verbose_name = 'Active')
    created_at = models.DateTimeField(verbose_name='Created at')
    project_uuid = models.CharField(max_length=255, verbose_name='Project UUID')

    class Meta:
        managed = False
        db_table = 'devices-by-projects'
        verbose_name = _('Device')
        ordering = ['wifi_mac']

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

