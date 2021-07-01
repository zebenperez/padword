from django.db import models
from django.utils.translation import ugettext as _

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
        return []

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

