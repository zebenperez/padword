from django.db import models
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.utils.translation import ugettext as _
from padword.commons import show_exc
from .lock_lib import ShLock
import datetime
import requests

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
    uuid = models.CharField(max_length=255, verbose_name='UUID', default="", unique=True)
    name = models.CharField(max_length=255, verbose_name='Name', default="")
    longitude = models.CharField(max_length=255, verbose_name='Longitud', default="", blank=True)
    latitude = models.CharField(max_length=255, verbose_name='Latitud', default="", blank=True)
    used_languages = models.CharField(max_length=255, verbose_name=_('Used Languages'), default="ES", blank=True)
    default_language = models.CharField(max_length=255, verbose_name='Idioma por defecto', default="ES", blank=True)
    currency = models.CharField(max_length=255, verbose_name='Moneda', default="EUR", blank=True)
    radius = models.IntegerField(verbose_name = 'Radio (Km)', default=100)
    active = models.IntegerField(verbose_name = 'Active', default=1)
    created_at = models.DateTimeField(verbose_name='Created at', default=datetime.datetime.now)

    company = models.ForeignKey(Company, verbose_name = 'Company', on_delete=models.SET_NULL, null=True)

    class Meta:
        if (len(settings.DATABASES) > 1):
            managed = False
            db_table = 'projects'
        verbose_name = _('Project')
        ordering = ['company__name', 'name']

    def __str__(self):
        return self.name

    @property
    def get_languages(self):
        try:
            #print (self.used_languages)
            return (self.used_languages.upper().replace(' ','').split(','))
        except Exception as e:
            print (show_exc(e))
            return (['ES'])

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

    def get_first_menu(self, username):
        pu = ProjectUser.objects.filter(username=username, project_uuid=self.uuid).first()
        if pu == None or len(pu.menus) == 0:
            return ""
        return pu.menus.split(";")[0]

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

def upload_image(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "users/images/%s" % (instance.id)
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

class ProjectUser(models.Model):
    #channels = models.ManyToManyField(Channel, verbose_name=_("Channels"), blank=True)
    project_uuid = models.CharField(max_length = 255, verbose_name= _('Project UUID'), default='admin')
    username = models.CharField(max_length = 255, verbose_name= _('Username'), default='admin')
    menus = models.CharField(max_length = 1000, verbose_name= _('Menus'), default='orders;guests;notifications')
    image = models.ImageField(upload_to=upload_image, blank=True, verbose_name="Imagen de perfil", help_text="Select file to upload")

    class Meta:
        verbose_name = _('Project user')

    @property
    def user(self):
        try:
            return User.objects.get(username=self.username)
        except:
            return None

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

    @staticmethod
    def get_or_create_project_user(project_uuid, email):
        try:
            user = User.objects.get(username=email)
        except:
            try:
                projects_group = Group.objects.get(name='projects') 
                user = User.objects.create_user(email, email=email)
                projects_group.user_set.add(user)
            except:
                return None
        pu, created = ProjectUser.objects.get_or_create(project_uuid=project_uuid, username=user.username)
        return user

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
    updated_at = models.DateTimeField(verbose_name=_('Updated at'), default=datetime.datetime.now)
    #channel_id = models.CharField(max_length=255, verbose_name='Channel ID', default="")

    channel = models.ForeignKey(Channel, verbose_name=_('Channel'), on_delete=models.SET_NULL, null=True, to_field='uuid')

    class Meta:
        if (len(settings.DATABASES) > 1):
            managed = False
            db_table = 'devices'
        verbose_name = _('Device')
        ordering = ['-updated_at', 'imei']

    @property
    def project(self):
        try:
            return self.channel.project
        except Exception as e:
            return (Project(uuid='0000-0000-00000000', name='UNDEFINED'))

    @property
    def project_uuid(self):
        try:
            return self.channel.project.uuid
        except Exception as e:
            return ('0000-0000-00000000')

    @classmethod
    def by_project(cls, project):
        try:
            #items = Device.objects.none()
            #for project in projects:
            #    items = items.union(Device.objects.filter(channel__project__uuid = project.uuid))
            #return (items)
            return Device.objects.filter(channel__project=project)
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
    def by_channel(cls, channel):
        try:
            #items = Device.objects.none()
            #for channel in channels:
            #    items = items.union(Device.objects.filter(channel_id = channel.id))
            #return (items)
            return Device.objects.filter(channel=channel)
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

class Lock(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    alias = models.CharField(max_length=255, verbose_name=_('Alias'), default="", null=True)
    room = models.CharField(max_length=255, verbose_name=_('Room'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except Exception as e:
            return None

    @property
    def state(self):
        obj = ShLock()
        state = obj.get_lock_state(self.uuid)
        return _("unlock") if state != 0 else _("lock")

    @property
    def charge(self):
        obj = ShLock()
        return obj.get_lock_charge(self.uuid)

    def set_code(self, code, start_date, end_date):
        obj = ShLock()
        return obj.set_lock_code(self.uuid, code, start_date, end_date)

    def change_code(self, code_id, new_code, start_date, end_date):
        obj = ShLock()
        return obj.change_lock_code(self.uuid, code_id, new_code, start_date, end_date)

    def remove_code(self, code_id):
        obj = ShLock()
        return obj.remove_lock_code(self.uuid, code_id)

    def get_all_passcodes(self):
        obj = ShLock()
        return obj.get_lock_all_passcodes(self.uuid)

    def add_card(self, card_number, start_date, end_date):
        obj = ShLock()
        return obj.lock_add_card(self.uuid, card_number, start_date, end_date)

    def get_cards(self):
        url = 'https://euapi.ttlock.com/v3/identityCard/list'
        params = dict(
            clientId='c5cd9353990e4061a082a7a275897de1',
            accessToken='4719a3f737f7d1adafe139fbea20f6fb',
            lockId=int(self.uuid),
            pageNo=1,
            pageSize=100,
            date = int(round(datetime.datetime.now().timestamp() * 1000))
        )
        resp = requests.get(url=url, params=params)
        data = resp.json() # Check the JSON Response Content documentation below
        keycard_list = KeyCard.objects.none()
        keycard_numbers = []
        for keycard_json in data['list']:
            keycard_numbers.append(keycard_json['cardNumber'])
        keycard_list = KeyCard.objects.filter(bluetooth__in = keycard_numbers)
        return keycard_list

    def css_charge(self):
        if self.charge > 90:
            return "fa-battery-full perc-100"
        if self.charge > 75:
            return "fa-battery-three-quarters perc-75"
        if self.charge > 50:
            return "fa-battery-half perc-50"
        if self.charge > 25:
            return "fa-battery-quarter perc-25"
        return "fa-battery-exclamation perc-0"

    class Meta:
        verbose_name = _('Lock')

class Room(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    alias = models.CharField(max_length=255, verbose_name=_('Alias'), default="", null=True)
    number = models.CharField(max_length=255, verbose_name=_('Number'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
    parent = models.ForeignKey('self', verbose_name = 'Parent', on_delete=models.SET_NULL, null=True)

    def childrens(self):
        return Room.objects.filter(parent=self)

    @property
    def is_busy(self):
        from guest.models import Guest
        return Guest.objects.filter(project_id = self.project_uuid, room = self.number, check_in__lte = datetime.date.today(), check_out__gte = datetime.date.today()).exists()

    @property
    def current_guest(self):
        from guest.models import Guest
        return Guest.objects.filter(project_id = self.project_uuid, room = self.number, check_in__lte = datetime.date.today(), check_out__gte = datetime.date.today()).order_by('pk').last()

    @property
    def state(self):
        if self.is_busy:
            return ('lock text-danger')
        return ('unlock text-success')

    def get_locks(self):
        return Lock.objects.filter(project_uuid = self.project_uuid, room = self.number).order_by('pk')

    def get_cards(self):
        cards = KeyCard.objects.none()
        for lock in self.get_locks():
            cards = cards or lock.get_cards()
        return (cards)

class KeyCard(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    bluetooth = models.CharField(max_length=255, verbose_name=_('Bluetooth Code'), default="")
    cardreader = models.CharField(max_length=255, verbose_name=_('Card Reader Code'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
    lock = models.ForeignKey(Lock, verbose_name = _('Lock'), on_delete=models.SET_NULL, null=True)

