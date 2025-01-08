from django.db import models
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.utils.translation import ugettext as _

from padword.commons import show_exc, get_int, new_ui_slug, date_to_utc, date_to_local
from .lock_lib import ShLock
from sensibo.sensibo_lib import ShSensibo
from sensibo.models import ProjectSensiboUser
from connector.models import ProjectAvantioUser, ProjectAvaibookUser, ProjectWinhotelUser, ProjectMewsUser

import datetime, pytz
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

def upload_logo(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "projects/logo/%s" % (instance.id)
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

class Project(models.Model):
    uuid = models.CharField(max_length=255, verbose_name='UUID', default="", unique=True)
    name = models.CharField(max_length=255, verbose_name='Name', default="")
    prefix = models.CharField(max_length=10, verbose_name='Prefix', default="")
    longitude = models.CharField(max_length=255, verbose_name='Longitud', default="", blank=True)
    latitude = models.CharField(max_length=255, verbose_name='Latitud', default="", blank=True)
    used_languages = models.CharField(max_length=255, verbose_name=_('Used Languages'), default="ES", blank=True)
    default_language = models.CharField(max_length=255, verbose_name='Idioma por defecto', default="ES", blank=True)
    currency = models.CharField(max_length=255, verbose_name='Moneda', default="EUR", blank=True)
    time_zone = models.CharField(max_length=50, verbose_name='Time zone', default="+00:00")
    time_zone_name = models.CharField(max_length=50, verbose_name='Time zone name', default="")
    radius = models.IntegerField(verbose_name='Radio (Km)', default=100)
    active = models.IntegerField(verbose_name='Active', default=1)
    guest_delete = models.IntegerField(verbose_name='Delete guest after', default=90)
    created_at = models.DateTimeField(verbose_name='Created at', default=datetime.datetime.now)
    expiration = models.DateTimeField(verbose_name='Expiration', default=datetime.datetime.now)

    logo = models.ImageField(upload_to=upload_logo, blank=True, verbose_name="Logo", help_text="Select file to upload")
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

    @property
    def get_rooms(self):
        return Room.objects.filter(project_uuid = self.uuid)

    @property
    def lock_access_token(self):
        plu = ProjectLockUser.objects.filter(project_uuid=self.uuid).first()
        return plu.token if plu != None and plu.token != "" else ""

    @property
    def sensibo_api_key(self):
        psu = ProjectSensiboUser.objects.filter(project_uuid=self.uuid).first()
        return psu.api_key if psu != None and psu.api_key != "" else ""

    @property
    def avantio_user(self):
        return ProjectAvantioUser.objects.filter(project_uuid=self.uuid).first()

    @property
    def avaibook_user(self):
        return ProjectAvaibookUser.objects.filter(project_uuid=self.uuid).first()

    @property
    def winhotel_user(self):
        return ProjectWinhotelUser.objects.filter(project_uuid=self.uuid).first()

    @property
    def mews_user(self):
        print(ProjectMewsUser.objects.filter(project_uuid=self.uuid).first())
        print(ProjectMewsUser.objects.all())
        for p in ProjectMewsUser.objects.all():
            print(p)
        return ProjectMewsUser.objects.filter(project_uuid=self.uuid).first()

    @property
    def invitations(self):
        return Invitation.objects.filter(project_uuid=self.uuid)

    def get_first_menu(self, username):
        pu = ProjectUser.objects.filter(username=username, project_uuid=self.uuid).first()
        #if pu == None or len(pu.menus) == 0:
        if pu == None:
            return ""
        menu_mod = pu.menus_mod.first()
        if menu_mod != None and menu_mod.menu != None:
            return menu_mod.menu
        if len(pu.menus) > 0:
            return pu.menus.split(";")[0]
        return ""

    def gateway_list(self):
        obj = ShLock(self.lock_access_token)
        return obj.get_gateways()

    def gateway_lock_list(self, gateway_id):
        obj = ShLock(self.lock_access_token)
        return obj.get_gateway_locks(gateway_id)

    def ekey_list(self):
        obj = ShLock(self.lock_access_token)
        return obj.get_ekeys()

    def get_keycards(self):
        return KeyCard.objects.filter(project_uuid=self.uuid)

    def sensibo_device_list(self):
        obj = ShSensibo(self.sensibo_api_key)
        #return obj.get_devices()
        d_list = obj.get_devices()
        device_list = []
        for key, value in d_list.items():
            device_list.append({'name': key, 'uid': value})
        return device_list

    def sensibo_get_measurement(self, device_uid):
        obj = ShSensibo(self.sensibo_api_key)
        #return obj.get_measurement(device_uid)
        measurement = obj.get_measurement(device_uid)
        node = {}
        if len(measurement) > 0:
            node["temperature"] = measurement[0]["temperature"] if "temperature" in measurement[0] else ""
            node["humidity"] = measurement[0]["humidity"] if "humidity" in measurement[0] else ""
            node["feels_like"] = measurement[0]["feelsLike"] if "feelsLike" in measurement[0] else ""
            node["rssi"] = measurement[0]["rssi"] if "rssi" in measurement[0] else ""
            node["motion"] = measurement[0]["motion"] if "motion" in measurement[0] else ""
            node["room_occupied"] = measurement[0]["roomIsOccupied"] if "roomIsOccupied" in measurement[0] else ""
        return node

    def sensibo_get_measurement_history(self, device_uid):
        obj = ShSensibo(self.sensibo_api_key)
        #return obj.get_measurement(device_uid)
        measurement = obj.get_measurement_history(device_uid)
        node = {"temperature": []}
        for item in measurement["temperature"]:
            print(item)
            temp = {"time": item["time"], "value": item["value"]}
            node["temperature"].append(temp)
        return node


    def sensibo_get_ac_state(self, device_uid):
        obj = ShSensibo(self.sensibo_api_key)
        #return obj.get_ac_state(device_uid)
        ac_state = obj.get_ac_state(device_uid)
        node = {}
        if len(ac_state) > 0 and "acState" in ac_state[0]:
            node["on"] = ac_state[0]["acState"]["on"] if "on" in ac_state[0]["acState"] else ""
            node["mode"] = ac_state[0]["acState"]["mode"] if "mode" in ac_state[0]["acState"] else ""
            node["fan_level"] = ac_state[0]["acState"]["fanLevel"] if "fanLevel" in ac_state[0]["acState"] else ""
            node["swing"] = ac_state[0]["acState"]["swing"] if "swing" in ac_state[0]["acState"] else ""
            node["light"] = ac_state[0]["acState"]["light"] if "light" in ac_state[0]["acState"] else ""
        return node

    def sensibo_change_ac_state(self, device_uid, ac_state):
        obj = ShSensibo(self.sensibo_api_key)
        return obj.change_ac_state(device_uid, ac_state)

    def sensibo_change_ac_state_param(self, device_uid, ac_state, param_name, param_value):
        obj = ShSensibo(self.sensibo_api_key)
        return obj.change_ac_state_param(device_uid, ac_state, param_name, param_value)

    def gmt_date(self, date, room=None):
        try:
            if room != None and room.time_zone_name != "":
                gmt_date = date_to_utc(date, room.time_zone_name)
            elif self.time_zone_name != "":
                gmt_date = date_to_utc(date, self.time_zone_name)
            else:
                time_zone = self.time_zone.split(":")
                plus = True if "+" in time_zone[0] else False
                hour = int(time_zone[0]) * -1 if plus else int(time_zone[0])
                minutes = int(time_zone[1]) * -0.6 if plus else int(time_zone[1]) * 0.6

                gmt_date = date + datetime.timedelta(hours=hour) + datetime.timedelta(minutes=minutes)
            return gmt_date
        except Exception as e:
            print(e)
            return date

    def local_date(self, date, room=None):
        try:
            if room != None and room.time_zone_name != "":
                local_date = date_to_local(date, room.time_zone_name)
            elif self.time_zone_name != "":
                local_date = date_to_local(date, self.time_zone_name)
            else:
                time_zone = self.time_zone.split(":")
                plus = True if "+" in time_zone[0] else False
                hour = int(time_zone[0]) if plus else int(time_zone[0]) * -1
                minutes = int(time_zone[1]) * 0.6 if plus else int(time_zone[1]) * -0.6

                local_date = date + datetime.timedelta(hours=hour) + datetime.timedelta(minutes=minutes)
            return local_date
        except Exception as e:
            return date

class ProjectLockUser(models.Model):
    username = models.CharField(max_length=255, verbose_name=_('Lock Username'), default="")
    password = models.CharField(max_length=255, verbose_name=_('Lock Password'), default="")
    token = models.CharField(max_length=255, verbose_name=_('Lock Token'), default="")
    refresh_token = models.CharField(max_length=255, verbose_name=_('Lock Refresh Token'), default="")
    uid = models.CharField(max_length=10, verbose_name=_('UID'), default="")
    expire = models.CharField(max_length=100, verbose_name=_('Expire'), default="")
    time_schedule_tasks = models.CharField(max_length=10, verbose_name=_('Time to schedule tasks'), default="")
    report_email = models.CharField(max_length=255, verbose_name=_('Report email'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
    text_to_share = models.TextField(verbose_name=_('Text to share'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

    @property
    def expire_date(self):
        try:
            return datetime.datetime.fromtimestamp(int(self.expire)).strftime("%d-%m-%Y, %I:%M:%S")
        except Exception as e:
            return "--"

    def get_token(self):
        obj = ShLock()
        res = obj.get_token(self.username, self.password)
        self.token = res["access_token"]
        self.refresh_token = res["refresh_token"]
        self.uid = res["uid"]
        self.expire = res["expires_in"]
        self.save()

    def get_new_token(self):
        obj = ShLock()
        res = obj.refresh_token(self.refresh_token)
        self.token = res["access_token"]
        self.refresh_token = res["refresh_token"]
        self.expire = res["expires_in"]
        self.save()

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

class Menu(models.Model):
    promo = models.BooleanField(verbose_name=_("Promo"), default = False)
    code = models.CharField(max_length = 255, verbose_name= _('Code'), default='')
    name = models.CharField(max_length = 255, verbose_name= _('Name'), default='')
    url = models.CharField(max_length = 255, verbose_name= _('Url'), default='')
    ico = models.CharField(max_length = 255, verbose_name= _('Icono'), default='')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Menu')

def upload_image(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "users/images/%s" % (instance.id)
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

class ProjectUser(models.Model):
    #channels = models.ManyToManyField(Channel, verbose_name=_("Channels"), blank=True)
    project_uuid = models.CharField(max_length = 255, verbose_name= _('Project UUID'), default='')
    username = models.CharField(max_length = 255, verbose_name= _('Username'), default='')
    menus = models.CharField(max_length = 1000, verbose_name= _('Menus'), default='orders;guests;notifications', blank=True)
    menus_promo = models.CharField(max_length = 1000, verbose_name= _('Menus Promo'), default='', blank=True)
    image = models.ImageField(upload_to=upload_image, blank=True, verbose_name="Imagen de perfil", help_text="Select file to upload")
    #menus_mod = models.ManyToManyField(Menu, verbose_name=_("Menus"), blank=True, related_name="menus")

    def __str__(self):
        return self.username

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

class ProjectUserMenu(models.Model):
    order = models.IntegerField(verbose_name=_('Order'), default=0, null=True)
    menu = models.ForeignKey(Menu, verbose_name=_('Menu'), on_delete=models.SET_NULL, null=True)
    project_user = models.ForeignKey(ProjectUser, verbose_name=_('ProjectUser'), on_delete=models.CASCADE, null=True, related_name="menus_mod")

    def __str__(self):
        return str(self.order)

    class Meta:
        verbose_name = _('Project User Menu')
        ordering = ['order']


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

class Room(models.Model):
    order = models.IntegerField(verbose_name=_('Order'), default=0, null=True)
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    alias = models.CharField(max_length=255, verbose_name=_('Alias'), default="", null=True)
    number = models.CharField(max_length=255, verbose_name=_('Number'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
    lock_group_uuid = models.CharField(max_length=255, verbose_name=_('Lock Group UUID'), default="")
    time_zone_name = models.CharField(max_length=50, verbose_name='Time zone name', default="")
    #parent = models.ForeignKey('self', verbose_name = 'Parent', on_delete=models.SET_NULL, null=True)

    #def childrens(self):
    #    return Room.objects.filter(parent=self)

    @property
    def is_busy(self):
        from guest.models import Guest
        today = datetime.date.today()
        return Guest.objects.filter(project_id=self.project_uuid, room=self.number, check_in__lte=today, check_out__gte=today, deleted=0).exists()

    @property
    def current_guest(self):
        from guest.models import Guest
        today = datetime.date.today()
        return Guest.objects.filter(project_id=self.project_uuid, room=self.number, check_in__lte=today, check_out__gte=today).order_by('pk').last()

    @property
    def state(self):
        if self.is_busy:
            return ('lock text-danger')
        return ('unlock text-success')

    #@property
    #def floor(self):
    #    obj = self
    #    while obj.parent != None:
    #        obj = obj.parent
    #    return obj.alias

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

    #@property
    #def lock_group(self):
    #    try:
    #        return LockGroup.objects.get(uuid=self.lock_group_uuid)
    #    except:
    #        return None

    #def get_locks(self):
    #    return Lock.objects.filter(project_uuid = self.project_uuid, room = self.number).order_by('pk') if self.number != "" else []

    def set_locks_group(self, val, lock_list):
        #for lock in self.get_locks():
        for lock in lock_list:
            lock.group_uuid = val
            lock.save()
            lock.set_group()

    def unassign_locks(self, lock_list):
        #lock_list = Lock.objects.filter(project_uuid = self.project_uuid, room = self.number).order_by('pk')
        for lock in lock_list:
            lock.room = ""
            lock.save()

    #def get_cards(self):
    #    cards = KeyCard.objects.none()
    #    for lock in self.get_locks():
    #        cards = cards or lock.get_cards()
    #    return (cards)

    class Meta:
        ordering = ["order"]

class Waiter(models.Model):
    uuid = models.CharField(max_length = 255, verbose_name= _('UUID'), default=new_ui_slug)
    project_uuid = models.CharField(max_length = 255, verbose_name= _('Project UUID'), default='')
    username = models.CharField(max_length = 255, verbose_name= _('Username'), default='')

    class Meta:
        verbose_name = _('Waiter')

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

class Invitation(models.Model):
    uuid = models.CharField(max_length = 255, verbose_name= _('UUID'), default=new_ui_slug)
    project_uuid = models.CharField(max_length = 255, verbose_name= _('Project UUID'), default='')
    name = models.CharField(max_length = 255, verbose_name= _('Name'), default='')

    class Meta:
        verbose_name = _('Invitation account')

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


class Module(models.Model):
    code = models.CharField(max_length = 255, verbose_name= _('Code'), default='')
    name = models.CharField(max_length = 255, verbose_name= _('Name'), default='')
    desc = models.TextField(verbose_name= _('Description'), default='')

    class Meta:
        verbose_name = _('Module')


