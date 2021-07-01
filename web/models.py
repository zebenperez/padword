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

    @property
    def get_devices(self):
        return []
