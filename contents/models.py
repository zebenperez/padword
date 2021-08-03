from django.db import models
from django.utils.translation import ugettext as _
from padword.commons import show_exc

from web.models import Channel, Project

# Create your models here.

class Category(models.Model):
    ALLOWCHOICES = (('yes','Yes'), ('no','No'), ('inherit', 'Inherit'),)
    ISACTIVECHOICES = ((0,'No'), (1,'Yes'),)

    uuid = models.CharField(max_length=36, verbose_name='UUID')
    #parent_uuid = models.CharField(max_length=36, verbose_name='UUID Parent', blank=True, null=True)
    parent_uuid = models.ForeignKey('Category', db_column = 'parent_uuid', to_field='uuid', on_delete=models.SET_NULL, null=True)
    project_uuid = models.CharField(max_length=36, verbose_name='UUID Project')
    place_uuid = models.CharField(max_length=36, verbose_name='UUID Place', blank=True, null=True)
    name = models.TextField(verbose_name='Name')
    description = models.TextField(verbose_name='Description')
    translation = models.TextField(verbose_name='Translation')
    allow_reservation = models.CharField(max_length='10', choices=ALLOWCHOICES, verbose_name='Allow Reservations', blank=True, null=True)
    minimum_reservation = models.IntegerField(verbose_name='Minimum Reservation', blank=True, null=True)
    supplement_cost = models.TextField(verbose_name='Supplement Cost', blank=True, null=True)
    emergency_supplement_cost = models.TextField(verbose_name='Emergency Supplement Cost', blank=True, null=True)
    icon = models.TextField(verbose_name='Icon', blank=True, null=True)
    rank = models.IntegerField(verbose_name='Rank', default=0)
    is_active = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Active', default=0)
    created_at = models.DateTimeField(verbose_name='Created')
    updated_at = models.DateTimeField(verbose_name='Updated')
    upload = models.CharField(max_length=255, verbose_name='Upload', blank=True, null=True)
    icon_type = models.CharField(max_length=50, verbose_name='Icon Type', blank=True, null=True)
    reservation_form_active = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Reservation Form Active', default=0)
    reservation_form = models.TextField(verbose_name='Reservation Form', blank=True, null=True, default='{}')
    coin = models.CharField(max_length=50, verbose_name='Coin', blank=True, null=True, default="Euro")
    items_reservation = models.TextField(verbose_name='Items Reservation', blank=True, null=True)
    schedules = models.TextField(verbose_name='Schedules', blank=True, null=True)
    extra_charge = models.TextField(verbose_name='Extra Charge', blank=True, null=True)
    minimum_amount_order = models.IntegerField(verbose_name='Minimum Amount Order', default=0)
    internal = models.TextField(verbose_name='Internal', blank=True, null=True)

    @property
    def parent(self):
        try:
            return Category.get(uuid = self.parent_uuid)
        except Exception as e:
            return Category(name='None', uuid='none')

    @property
    def project(self):
        try:
            return Project.objects.get(uuid = self.project_uuid)
        except Exception as e:
            return Project(name='UNKNOWN')

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

    class Meta:
        managed = False
        db_table = 'categories'
        verbose_name = _('Category')
