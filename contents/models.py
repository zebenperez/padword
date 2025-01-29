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

def upload_category_file(instance, filename):
    folder = "contents/categories/files/%s" % (instance.category.id)
    return '/'.join(['%s' % (folder), filename])
    #ascii_filename = str(filename.encode('ascii', 'ignore'))
    #instance.filename = ascii_filename
    #return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

def upload_item_image(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "contents/items/images/%s" % (instance.id)
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

def upload_pos_image(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "contents/point_of_sales/images/%s" % (instance.id)
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])


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
    def get_items_favorites(self):
        return [item.item for item in ItemInCat.objects.filter(category = self, item__is_active=True, item__favorite=True).order_by('position')]

    @property
    def get_childrens(self):
        try:
            #return Category.objects.filter(parent = self, is_active = True)
            return Category.objects.filter(parent = self)
        except Exception as e:
            print (showx_exc(e))
            return Category.objects.none()

    @property
    def get_active_childrens(self):
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

    def get_file_by_order(self, order):
        return self.files.filter(order=order).first()

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

class CategoryFile(models.Model):
    order = models.IntegerField(verbose_name=_('Order'), default=0)
    file = models.FileField(upload_to=upload_category_file, verbose_name=_("File"), blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, related_name="files")

    class Meta:
        verbose_name = _('Category File')
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

class PaymentType(models.Model):
    code = models.SlugField(verbose_name="Codigo", max_length=50, unique="True")
    name = models.CharField(verbose_name="Nombre", max_length=150, blank=True, null=True)
    icon = models.ImageField(verbose_name="Icono", upload_to=feature_icon, blank=True, null=True)
    icon_off = models.ImageField(verbose_name="Icono off", upload_to=feature_icon, blank=True, null=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Payment type"
        verbose_name_plural = "Payment types"

class CategoryPaymentType(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, related_name="payment_types")
    payment_type = models.ForeignKey(PaymentType, on_delete=models.SET_NULL, null=True, related_name="categories")

    class Meta:
        verbose_name = "Payment Type Category"
        verbose_name_plural = "Payment Types Category"



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
    favorite = models.BooleanField(default=False, verbose_name=_("Favorite"))
    especial = models.BooleanField(default=False, verbose_name=_("Especial"))
    ext_id = models.IntegerField(verbose_name=_('External ID'), default=0, blank=True)

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
    def category(self):
        try:
            item = ItemInCat.objects.filter(item=self).first()
            return item.category
        except Exception as e:
            return None

    @property
    def project(self):
        try:
            #return Project.objects.get(uuid = self.category.project)
            item = ItemInCat.objects.filter(item=self).first()
            return item.category.project
        except Exception as e:
            return Project(name='UNKNOWN')

    @property
    def currency(self):
        try:
            return self.project.currency
        except Exception as e:
            return "€"


    def get_price(self, code, band=None):
        ip = self.prices.filter(regime_code=code).first()

        #Regime price not defined
        if ip == None:
            ip = ItemPrice.objects.create(item=self, regime_code=code, price=self.price)

        #Credit 0
        if code == "TI" and band != None and band.type != None and band.type.code == "02" and ip.price > 0:
            return None

        return ip.price

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

class ItemImage(models.Model):
    order = models.IntegerField(verbose_name=_('Order'), default=0)
    image = models.ImageField(upload_to=upload_item_image, verbose_name=_("Image"), blank=True, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name=_("Item"), blank=True, null=True, related_name="images")

    class Meta:
        verbose_name = _('Item Image')
        ordering = ['order']

class ShoppingCart(models.Model):
    form_instance_id = models.IntegerField(verbose_name=_("Form Instance"), default=0)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, verbose_name=_("Item"), blank=True, null=True)
    options = models.ManyToManyField(OptionItem, blank=True, verbose_name=_("Options"))
    comments = models.TextField(verbose_name = _("Comments"), default="")

    category = models.CharField(verbose_name="Categoría", max_length=250, blank=True, null=True)
    name = models.CharField(verbose_name="Nombre", max_length=250, blank=True, null=True)
    price = models.FloatField(verbose_name='Price', default=0, null=True, blank=True)
    low_price = models.FloatField(verbose_name='Low Price', default=-1, null=True, blank=True)
    discount = models.FloatField(verbose_name='Discount', default=0, null=True, blank=True)
    total_price = models.FloatField(verbose_name='Total Price', default=-1, null=True, blank=True)

    @property
    def get_low_price(self):
        return "" if self.low_price == -1 else self.low_price

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

def upload_item_banner(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "contents/items/banners/%s" % (instance.id)
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

class ItemPromo(models.Model):
    ini_date = models.DateTimeField(_('Ini date'), default=datetime.datetime.now, null=True)
    end_date = models.DateTimeField(_('End date'), default=datetime.datetime.now, null=True)
    banner = models.ImageField(upload_to=upload_item_banner, verbose_name=_("Image"), blank=True, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, related_name="promos")

    class Meta:
        verbose_name = "Item Promo"
        verbose_name_plural = "Item Promo"

    @staticmethod
    def get_current(project_uuid):
        now = datetime.datetime.now()
        cat_uuid_list = list(Category.objects.filter(project_uuid=project_uuid).values_list('uuid', flat=True))
        ic_list = list(ItemInCat.objects.filter(category__in=cat_uuid_list).values_list('item', flat=True))
        return ItemPromo.objects.filter(item__uuid__in = ic_list)

class ItemPrice(models.Model):
    price = models.FloatField(verbose_name='Price', default=0, null=True, blank=True)
    regime_code = models.CharField(max_length=50, verbose_name= _('Regime code'), default='')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, related_name="prices")

    class Meta:
        verbose_name = "Item Price"
        verbose_name_plural = "Item Prices"

class CategoryUser(models.Model):
    view_cat = models.BooleanField(default=False, verbose_name=_("View category"))
    remove_cat = models.BooleanField(default=False, verbose_name=_("Remove category"))
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

    #@property
    #def category(self):
    #    try:
    #        return Category.objects.get(uuid=self.category_uuid)
    #    except:
    #        return None

    @property
    def categories(self):
        try:
            return Category.objects.filter(uuid__in=self.category_uuid.split(","))
        except:
            return []

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

class PointOfSale(models.Model):
    order = models.IntegerField(verbose_name=_('Order'), default=0)
    uuid = models.CharField(max_length = 255, verbose_name= _('UUID'), default="")
    name = models.CharField(verbose_name="Nombre", max_length=150, blank=True, null=True, default="")
    code1 = models.CharField(verbose_name="Código 1", max_length=10, blank=True, null=True, default="")
    code2 = models.CharField(verbose_name="Código 2", max_length=10, blank=True, null=True, default="")
    code3 = models.CharField(verbose_name="Código 3", max_length=10, blank=True, null=True, default="")
    ext_code = models.CharField(verbose_name="Código externo", max_length=10, blank=True, null=True, default="")
    suffix = models.CharField(verbose_name="Sufijo fichero", max_length=50, blank=True, null=True, default="")
    image = models.ImageField(upload_to=upload_pos_image, verbose_name=_("Image"), blank=True, null=True)
    project_uuid = models.CharField(max_length=36, verbose_name='UUID Project', default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid = self.project_uuid)
        except Exception as e:
            return None

    @property
    def regular_name(self):
        return self.name.replace(" ", "").lower()

    def get_categories(self):
        return [item.category for item in self.categories.all()]

    class Meta:
        verbose_name = _("Point of sale")
        verbose_name_plural = _("Points of sales")
        ordering = ['order']

class PointOfSaleCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_("Category"), related_name="point_of_sales")
    point_of_sale = models.ForeignKey(PointOfSale, on_delete=models.CASCADE, verbose_name=_("Point of sale"), related_name="categories")

class Table(models.Model):
    uuid = models.CharField(max_length = 255, verbose_name= _('UUID'), default="")
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    point_of_sale = models.ForeignKey(PointOfSale, on_delete=models.CASCADE, verbose_name=_("Point of sale"), related_name="tables")

    def __str__(self):
        return self.name
