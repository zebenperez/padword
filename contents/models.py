from django.db import models
from django.utils.translation import ugettext as _
from padword.commons import show_exc, translate
from django.conf import settings

from web.models import Channel, Project

# Create your models here.

# class CategoryOld(models.Model):
#     ALLOWCHOICES = (('yes','Yes'), ('no','No'), ('inherit', 'Inherit'),)
#     ISACTIVECHOICES = ((0,'No'), (1,'Yes'),)
# 
#     uuid = models.CharField(max_length=36, verbose_name='UUID', unique=True)
#     #parent_uuid = models.CharField(max_length=36, verbose_name='UUID Parent', blank=True, null=True)
#     parent= models.ForeignKey('Category', db_column = 'parent_uuid', to_field='uuid', on_delete=models.SET_NULL, null=True)
# #     project = models.ForeignKey('web.Project', db_column = 'project_uuid', to_field='uuid', on_delete=models.SET_NULL, null=True)
#     project_uuid = models.CharField(max_length=36, verbose_name='UUID Project')
#     place_uuid = models.CharField(max_length=36, verbose_name='UUID Place', blank=True, null=True)
#     name = models.TextField(verbose_name='Name')
#     description = models.TextField(verbose_name='Description')
#     translation = models.TextField(verbose_name='Translation')
#     allow_reservation = models.CharField(max_length=10, choices=ALLOWCHOICES, verbose_name='Allow Reservations', blank=True, null=True)
#     minimum_reservation = models.IntegerField(verbose_name='Minimum Reservation', blank=True, null=True)
#     supplement_cost = models.TextField(verbose_name='Supplement Cost', blank=True, null=True)
#     emergency_supplement_cost = models.TextField(verbose_name='Emergency Supplement Cost', blank=True, null=True)
#     icon = models.TextField(verbose_name='Icon', blank=True, null=True)
#     rank = models.IntegerField(verbose_name='Rank', default=0)
#     is_active = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Active', default=0)
#     created_at = models.DateTimeField(verbose_name='Created')
#     updated_at = models.DateTimeField(verbose_name='Updated')
#     upload = models.CharField(max_length=255, verbose_name='Upload', blank=True, null=True)
#     icon_type = models.CharField(max_length=50, verbose_name='Icon Type', blank=True, null=True)
#     reservation_form_active = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Reservation Form Active', default=0)
#     reservation_form = models.TextField(verbose_name='Reservation Form', blank=True, null=True, default='{}')
#     coin = models.CharField(max_length=50, verbose_name='Coin', blank=True, null=True, default="Euro")
#     items_reservation = models.TextField(verbose_name='Items Reservation', blank=True, null=True)
#     schedules = models.TextField(verbose_name='Schedules', blank=True, null=True)
#     extra_charge = models.TextField(verbose_name='Extra Charge', blank=True, null=True)
#     minimum_amount_order = models.IntegerField(verbose_name='Minimum Amount Order', default=0)
#     internal = models.TextField(verbose_name='Internal', blank=True, null=True)
# 
#     @property
#     def project(self):
#         try:
#             return Project.get(uuid = self.project_uuid)
#         except Exception as e:
#             return Project(name='None', uuid='none')
# 
#     @property
#     def get_items(self):
#         try:
#             return Item.objects.filter(category = self)
#         except Exception as e:
#             return Item.objects.none()
# 
#     @property
#     def get_childrens(self):
#         try:
#             return Category.objects.filter(parent = self)
#         except Exception as e:
#             return Category.objects.none()
# 
#     @property
#     def is_parent(self):
#         try:
#             return Category.objects.filter(parent = self).exists() or Item.objects.filter(category = self).exists()
#         except Exception as e:
#             print (show_exc(e))
#             return False
# 
# 
#     class Meta:
#         if len(settings.DATABASES) > 1:
#             managed = False
#             db_table = 'categories'
#         verbose_name = _('Category')
# 
# 
# class ItemOld(models.Model):
#     ALLOWCHOICES = (('yes','Yes'), ('no','No'), ('inherit', 'Inherit'),)
#     ISACTIVECHOICES = ((0,'No'), (1,'Yes'),)
# 
#     uuid = models.CharField(max_length=36, verbose_name='UUID', unique=True)
#     category= models.ForeignKey('Category', db_column = 'category_uuid', to_field='uuid', on_delete=models.SET_NULL, null=True)
#     name = models.TextField(verbose_name='Name')
#     title = models.TextField(verbose_name='Title')
#     description = models.TextField(verbose_name='Description')
#     translation = models.TextField(verbose_name='Translation')
#     price = models.TextField(verbose_name='Price', null = True, blank = True)
#     time_reservation = models.TextField(verbose_name='Time Reservation', null=True, blank = True)
#     allergens = models.TextField(verbose_name='Allergens', blank=True, null=True)
#     gallery = models.TextField(verbose_name='Gallery', blank=True, null=True)
#     reservation_form = models.TextField(verbose_name='Reservation Form', blank=True, null=True, default='{}')
#     rank = models.IntegerField(verbose_name='Rank', default=0)
#     is_event = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Event', default=0)
#     is_active = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Active', default=0)
#     created_at = models.DateTimeField(verbose_name='Created')
#     updated_at = models.DateTimeField(verbose_name='Updated')
#     reservation_form_active = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Reservation Form Active', default=0)
#     extras = models.TextField(verbose_name='Extras', blank=True, null=True)
#     contains_allergens = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Active', default=0)
# 
#     @property
#     def project(self):
#         try:
#             return Project.objects.get(uuid = self.category.project)
#         except Exception as e:
#             return Project(name='UNKNOWN')
# 
#     @classmethod
#     def by_category(cls, categories):
#         try:
#             items = Item.objects.none()
#             if isinstance(categories, models.query.QuerySet):
#                 for cateory in categories:
#                     items = items.union(Item.objects.filter(category=category ))
#             else:
#                 items = Item.objects.filter(category = category)
#             return items
#         except Exception as e:
#             print (show_exc(e))
#             return Item.objects.none()
# 
#     class Meta:
#         if len(settings.DATABASES) > 1:
#             managed = False
#             db_table = 'items'
#         verbose_name = _('Item')

class Category(models.Model):
    ALLOWCHOICES = (('yes','Yes'), ('no','No'), ('inherit', 'Inherit'),)
    ISACTIVECHOICES = ((0,'No'), (1,'Yes'),)

    uuid = models.CharField(max_length=36, verbose_name='UUID', unique=True)
    #parent_uuid = models.CharField(max_length=36, verbose_name='UUID Parent', blank=True, null=True)
    parent= models.ForeignKey('Category', db_column = 'parent_uuid', to_field='uuid', on_delete=models.SET_NULL, null=True)
#     project = models.ForeignKey('web.Project', db_column = 'project_uuid', to_field='uuid', on_delete=models.SET_NULL, null=True)
    project_uuid = models.CharField(max_length=36, verbose_name='UUID Project')
    place_uuid = models.CharField(max_length=36, verbose_name='UUID Place', blank=True, null=True)
    name = models.TextField(verbose_name='Name')
    description = models.TextField(verbose_name='Description')
    translation = models.TextField(verbose_name='Translation')
    allow_reservation = models.CharField(max_length=10, choices=ALLOWCHOICES, verbose_name='Allow Reservations', blank=True, null=True)
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
    position = models.IntegerField(verbose_name=_('Position'), default=0)

    @property
    def active(self):
        try:
            return (self.is_active == 1)
        except Exception as e:
            print (show_exc(e))
            return False

    @property
    def project(self):
        try:
            return Project.objects.get(uuid = self.project_uuid)
        except Exception as e:
            return Project(name='None', uuid='none')

    @property
    def company(self):
        try:
            return self.project.company
        except Exception as e:
            return Project(name='None', uuid='none')

    @property
    def get_items(self):
        try:
            items_in_cat = ItemInCat.objects.filter(category = self).order_by('position')
            results = []
            for item in items_in_cat:
                results.append(item.item)
            return results
        except Exception as e:
            print (show_exc(e))
            return []

    @property
    def get_childrens(self):
        try:
            return Category.objects.filter(parent = self)
        except Exception as e:
            return Category.objects.none()

    @property
    def is_parent(self):
        try:
            return Category.objects.filter(parent = self).exists() or Item.objects.filter(category = self).exists()
        except Exception as e:
            print (show_exc(e))
            return False


    class Meta:
        db_table = 'categories_shidix'
        verbose_name = _('Category')

class Item(models.Model):
    ALLOWCHOICES = (('yes','Yes'), ('no','No'), ('inherit', 'Inherit'),)
    ISACTIVECHOICES = ((0,'No'), (1,'Yes'),)

    uuid = models.CharField(max_length=36, verbose_name='UUID', unique=True)
    #category= models.ForeignKey('Category', db_column = 'category_uuid', to_field='uuid', on_delete=models.SET_NULL, null=True)
    name = models.TextField(verbose_name='Name')
    title = models.TextField(verbose_name='Title')
    description = models.TextField(verbose_name='Description')
    translation = models.TextField(verbose_name='Translation')
    price = models.TextField(verbose_name='Price', null = True, blank = True)
    time_reservation = models.TextField(verbose_name='Time Reservation', null=True, blank = True)
    allergens = models.TextField(verbose_name='Allergens', blank=True, null=True)
    gallery = models.TextField(verbose_name='Gallery', blank=True, null=True)
    reservation_form = models.TextField(verbose_name='Reservation Form', blank=True, null=True, default='{}')
    rank = models.IntegerField(verbose_name='Rank', default=0)
    is_event = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Event', default=0)
    is_active = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Active', default=0)
    created_at = models.DateTimeField(verbose_name='Created')
    updated_at = models.DateTimeField(verbose_name='Updated')
    reservation_form_active = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Reservation Form Active', default=0)
    extras = models.TextField(verbose_name='Extras', blank=True, null=True)
    contains_allergens = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Active', default=0)

    @property
    def active(self):
        try:
            return (self.is_active == 1)
        except Exception as e:
            print (show_exc(e))
            return False

    @property
    def project(self):
        try:
            return Project.objects.get(uuid = self.category.project)
        except Exception as e:
            return Project(name='UNKNOWN')

    @classmethod
    def by_category(cls, categories):
        try:
            items = Item.objects.none()
            if isinstance(categories, models.query.QuerySet):
                for cateory in categories:
                    items = items.union(Item.objects.filter(category=category ))
            else:
                items = Item.objects.filter(category = category)
            return items
        except Exception as e:
            print (show_exc(e))
            return Item.objects.none()

    class Meta:
        db_table = 'items_shidix'
        verbose_name = _('Item')

class ItemInCat(models.Model):
    position = models.IntegerField('Position', default = 0)
    category = models.ForeignKey('Category', to_field='uuid', on_delete=models.SET_NULL, null=True)
    item     = models.ForeignKey('Item', to_field='uuid', on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'items_in_cat_shidix'
        verbose_name = _('Items in Category')

