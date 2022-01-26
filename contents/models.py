from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _

from padword.commons import show_exc, translate, normalize_str

from web.models import Channel, Project
import datetime


def image_file(instance, filename):
    #filename = normalize_str(filename)
    instance.filename = filename
    return '/'.join(['folder_images',instance.uuid, datetime.datetime.now().strftime("%Y%m%d%H%M%S") + filename])

def upload_category_image(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "contents/categories/images/%s" % (instance.id)
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

# Create your models here.
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

    show_img = models.BooleanField(default=False, help_text=_("Show image"), verbose_name="Show image")
    image = models.ImageField(upload_to=upload_category_image, verbose_name=_("Image"), blank=True, null=True)
    url = models.TextField(verbose_name='Url', blank=True, default="")

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
    def get_items_active(self):
        try:
            items_in_cat = ItemInCat.objects.filter(category = self).order_by('position')
            results = []
            for item in items_in_cat:
                if item.item.is_active:
                    results.append(item.item)
            return results
        except Exception as e:
            print (show_exc(e))
            return []

    @property
    def get_childrens(self):
        try:
            return Category.objects.filter(parent = self, is_active = True)
        except Exception as e:
            print (showx_exc(e))
            return Category.objects.none()

    @property
    def is_parent(self):
        try:
            return Category.objects.filter(parent = self).exists() or Item.objects.filter(category = self).exists()
        except Exception as e:
            print (show_exc(e))
            return False

    @property
    def get_parents_options(self):
        if self.parent is not None:
            parents_options = Category.objects.filter(pk=self.parent.pk)
        else:
            parents_options = Category.objects.none()
        return parents_options.union(Category.objects.filter(project_uuid = self.project_uuid, parent = self.parent))

    class Meta:
        db_table = 'categories_shidix'
        verbose_name = _('Category')
        ordering = ['position']

class CategoryImage(models.Model):
    order = models.IntegerField(verbose_name=_('Order'), default=0)
    image = models.ImageField(upload_to=upload_category_image, verbose_name=_("Image"), blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, related_name="images")

    class Meta:
        verbose_name = _('Category Image')
        ordering = ['order']

def feature_icon(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    return '/'.join(['features', ascii_filename])

class Feature(models.Model):
    code = models.SlugField(verbose_name="Codigo", max_length=50, unique="True")
    name = models.CharField(verbose_name="Nombre", max_length=150, blank=True, null=True)
    icon = models.ImageField(verbose_name="Icono", upload_to=feature_icon, blank=True, null=True)
    icon_off = models.ImageField(verbose_name="Icono off", upload_to=feature_icon, blank=True, null=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Característica"
        verbose_name_plural = "Características"

class CategoryFeature(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, related_name="features")
    feature = models.ForeignKey(Feature, on_delete=models.SET_NULL, null=True, related_name="categories")

    class Meta:
        verbose_name = "Característica Categoría"
        verbose_name_plural = "Características Categorías"



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
    image = models.ImageField(upload_to=image_file, verbose_name=_("Image"), blank=True, null=True)

    def __str__(self):
        return (translate(None,self.name))

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

class OptionItem(models.Model):
    ISACTIVECHOICES = ((0,'No'), (1,'Yes'),)

    uuid = models.CharField(max_length=36, verbose_name='UUID', unique=True)
    item = models.ForeignKey('Item', db_column = 'item_uuid', to_field='uuid', on_delete=models.CASCADE)
    name = models.TextField(verbose_name='Name')
    title = models.TextField(verbose_name='Title')
    description = models.TextField(verbose_name='Description')
    translation = models.TextField(verbose_name='Translation')
    price = models.TextField(verbose_name='Price', null = True, blank = True)
    allergens = models.TextField(verbose_name='Allergens', blank=True, null=True)
    is_active = models.IntegerField(choices=ISACTIVECHOICES, verbose_name='Active', default=0)
    position = models.IntegerField(verbose_name='Position', default=0)
    created_at = models.DateTimeField(verbose_name='Created')
    updated_at = models.DateTimeField(verbose_name='Updated')

    @property
    def active(self):
        try:
            return (self.is_active == 1)
        except Exception as e:
            print (show_exc(e))
            return False

    class Meta:
        db_table = 'option_item'
        verbose_name = _('Options in item')

class ShoppingCart(models.Model):
    form_instance_id = models.IntegerField(verbose_name=_("Form Instance"), default=0)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name=_("Item"), blank=True, null=True)
    options = models.ManyToManyField(OptionItem, blank=True, verbose_name=_("Options"))
    comments = models.TextField(verbose_name = _("Comments"), default="")

    class Meta:
        db_table = 'shopping_cart'
        verbose_name = _('Shopping Cart')

def allergen_icon(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    return '/'.join(['allergens', ascii_filename])

class Allergen(models.Model):
    code = models.SlugField(verbose_name="Codigo", max_length=50, unique="True")
    name = models.CharField(verbose_name="Nombre", max_length=150, blank=True, null=True)
    icon = models.ImageField(verbose_name="Icono", upload_to=allergen_icon, blank=True, null=True)
    icon_off = models.ImageField(verbose_name="Icono off", upload_to=allergen_icon, blank=True, null=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Alergeno"
        verbose_name_plural = "Alergeno"

class ItemAllergen(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, related_name="allergen_list")
    allergen = models.ForeignKey(Allergen, on_delete=models.SET_NULL, null=True, related_name="items")

    class Meta:
        verbose_name = "Item Alergeno"
        verbose_name_plural = "Item Alergeno"

class ItemExtra(models.Model):
    name = models.CharField(verbose_name="Nombre", max_length=150, blank=True, null=True, default="")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, related_name="extra_list")

    class Meta:
        verbose_name = "Item Extra"
        verbose_name_plural = "Item Extra"

class CategoryUser(models.Model):
    category_uuid = models.CharField(max_length = 255, verbose_name= _('Category UUID'), default='')
    username = models.CharField(max_length = 255, verbose_name= _('Username'), default='')

    class Meta:
        verbose_name = _('Category user')

    @property
    def user(self):
        try:
            return User.objects.get(username=self.username)
        except:
            return None

    @property
    def category(self):
        try:
            return Category.objects.get(uuid=self.category_uuid)
        except:
            return None

    @staticmethod
    def get_or_create_category_user(category_uuid, email):
        try:
            user = User.objects.get(username=email)
        except:
            try:
                categories_group = Group.objects.get(name='categories') 
                user = User.objects.create_user(email, email=email)
                categories_group.user_set.add(user)
            except:
                return None
        pu, created = CategoryUser.objects.get_or_create(category_uuid=category_uuid, username=user.username)
        return user


