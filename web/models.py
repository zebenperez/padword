from django.db import models
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.utils.translation import ugettext as _

from padword.commons import show_exc, get_int, new_ui_slug
from .lock_lib import ShLock
from sensibo.sensibo_lib import ShSensibo
from sensibo.models import ProjectSensiboUser
from connector.models import ProjectAvantioUser, ProjectAvaibookUser, ProjectWinhotelUser

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
    radius = models.IntegerField(verbose_name='Radio (Km)', default=100)
    active = models.IntegerField(verbose_name='Active', default=1)
    guest_delete = models.IntegerField(verbose_name='Delete guest after', default=90)
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

    def get_first_menu(self, username):
        pu = ProjectUser.objects.filter(username=username, project_uuid=self.uuid).first()
        if pu == None or len(pu.menus) == 0:
            return ""
        return pu.menus.split(";")[0]

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

    def gmt_date(self, date):
        try:
            time_zone = self.time_zone.split(":")
            plus = True if "+" in time_zone[0] else False
            hour = int(time_zone[0]) * -1 if plus else int(time_zone[0])
            minutes = int(time_zone[1]) * -0.6 if plus else int(time_zone[1]) * 0.6

            gmt_date = date + datetime.timedelta(hours=hour) + datetime.timedelta(minutes=minutes)

            #check daylight saving time
            #timeZone = pytz.timezone("Atlantic/Canary")
            #aware_dt = timeZone.localize(date)
            #if aware_dt.dst() != datetime.timedelta(0,0):
            #    gmt_date += datetime.timedelta(hours=-1)

            return gmt_date
        except Exception as e:
            return date

    def local_date(self, date):
        try:
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

#class ProjectSensiboUser(models.Model):
#    api_key = models.CharField(max_length=255, verbose_name=_('API KEY'), default="")
#    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
#
#    @property
#    def project(self):
#        try:
#            return Project.objects.get(uuid=self.project_uuid)
#        except:
#            return None
#

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
    project_uuid = models.CharField(max_length = 255, verbose_name= _('Project UUID'), default='')
    username = models.CharField(max_length = 255, verbose_name= _('Username'), default='')
    menus = models.CharField(max_length = 1000, verbose_name= _('Menus'), default='orders;guests;notifications')
    menus_promo = models.CharField(max_length = 1000, verbose_name= _('Menus Promo'), default='', blank=True)
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

#class Lock(models.Model):
#    last_update = models.DateTimeField(verbose_name=_('Last update'), default=datetime.datetime.now, null=True)
#    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
#    alias = models.CharField(max_length=255, verbose_name=_('Alias'), default="", null=True)
#    room = models.CharField(max_length=255, verbose_name=_('Room'), default="")
#    charge_cache = models.CharField(max_length=10, verbose_name=_('Charge cache'), default="")
#    state_cache = models.CharField(max_length=100, verbose_name=_('State cache'), default="")
#    gateway_cache = models.CharField(max_length=900, verbose_name=_('Gateway cache'), default="")
#    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
#    group_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
#
#    @property
#    def project(self):
#        try:
#            return Project.objects.get(uuid=self.project_uuid)
#        except Exception as e:
#            return None
#
#    @property
#    def group(self):
#        try:
#            return LockGroup.objects.get(uuid=self.group_uuid)
#        except Exception as e:
#            return None
#
#    @property
#    def room_obj(self):
#        return Room.objects.filter(project_uuid=self.project_uuid, number=self.room).first()
#
#    @property
#    def state(self):
#        now = pytz.utc.localize(datetime.datetime.now())
#        if ((now - self.last_update).seconds/60) > 15:
#            self.update_params()
#        return _("unlock") if get_int(self.state_cache) != 0 else _("lock")
#
#    @property
#    def charge(self):
#        now = pytz.utc.localize(datetime.datetime.now())
#        if ((now - self.last_update).seconds/60) > 15:
#            self.update_params()
#        return self.charge_cache
#
#    @property
#    def gateway(self):
#        now = pytz.utc.localize(datetime.datetime.now())
#        if ((now - self.last_update).seconds/60) > 15:
#            self.update_params()
#        return self.gateway_cache
#
#    def update_params(self):
#        obj = ShLock(self.project.lock_access_token)
#
#        state_cache = obj.get_lock_state(self.uuid)
#        charge_cache = obj.get_lock_charge(self.uuid)
#        gateway_cache = obj.get_lock_gateway(self.uuid)
#
#        self.state_cache = state_cache if "Error" not in str(state_cache) else ""
#        self.charge_cache = charge_cache if "Error" not in str(charge_cache) else ""
#        #self.gateway_cache = _("Connected") if len(gateway_cache["list"]) > 0 else _("Not connected")
#        self.gateway_cache = gateway_cache
#        self.last_update = pytz.utc.localize(datetime.datetime.now())
#        self.save()
#
#    def open_lock(self):
#        sh_lock = ShLock(self.project.lock_access_token)
#        return sh_lock.open_lock_by_id(self.uuid)
#
#    def set_code(self, code, start_date, end_date, name=""):
#        obj = ShLock(self.project.lock_access_token)
#        code_name = name if name != "" else self.alias
#        return obj.set_lock_code(self.uuid, code, code_name, start_date, end_date)
#
#    def get_code(self, code_type, start_date, end_date):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.get_lock_code(self.uuid, code_type, start_date, end_date)
#
#    def change_code(self, code_id, new_code, start_date, end_date):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.change_lock_code(self.uuid, code_id, new_code, start_date, end_date)
#
#    def remove_code(self, code_id):
#        key_code_list = self.keycodes.filter(code_id=code_id)
#        for key_code in key_code_list:
#            key_code.delete()
#        obj = ShLock(self.project.lock_access_token)
#        return obj.remove_lock_code(self.uuid, code_id)
#
#    def get_all_passcodes(self):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.get_lock_all_passcodes(self.uuid)
#
#    def add_card(self, card_number, start_date, end_date, name=""):
#        obj = ShLock(self.project.lock_access_token)
#        card_name = name if name != "" else self.alias
#        return obj.lock_add_card(self.uuid, card_number, card_name, start_date, end_date)
#
#    def remove_card(self, code_id):
#        key_card_list = self.keycards.filter(card_id=code_id)
#        for key_card in key_card_list:
#            key_card.delete()
#        obj = ShLock(self.project.lock_access_token)
#        return obj.remove_lock_card(self.uuid, code_id)
#
#    def get_all_cards(self):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.get_lock_all_cards(self.uuid)
#
#    def change_period_card(self, card_id, start_date, end_date):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.change_period_lock_card(self.uuid, card_id, start_date, end_date)
#
#    def set_group(self):
#        obj = ShLock(self.project.lock_access_token)
#        if self.group != None:
#            return obj.set_lock_group(self.uuid, self.group.remote_id)
#        else:
#            return obj.set_lock_group(self.uuid, "")
#
#    def add_ekey(self, username, key_name, start_date, end_date):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.send_lock_key(self.uuid, username, key_name, start_date, end_date)
#
#    def remove_ekey(self, ekey_id):
#        #key_code_list = self.ekeys.filter(ekey_id=ekey_id)
#        #for ekey in ekey_list:
#        #    ekey.delete()
#        obj = ShLock(self.project.lock_access_token)
#        return obj.remove_lock_key(self.uuid, ekey_id)
#
#    def get_all_ekeys(self):
#        #obj = ShLock()
#        #return obj.get_lock_all_keys(self.uuid)
#        return LockEkey.objects.filter(lock_uuid=self.uuid)
#
#    def get_gateway_name_by_id(self, gateway_id):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.get_gateway_name(self.uuid, gateway_id)
#
#    def get_all_records(self):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.get_lock_all_records(self.uuid)
#
#
#    def get_cards(self):
#        url = 'https://euapi.ttlock.com/v3/identityCard/list'
#        params = dict(
#            clientId='c5cd9353990e4061a082a7a275897de1',
#            accessToken='4719a3f737f7d1adafe139fbea20f6fb',
#            lockId=int(self.uuid),
#            pageNo=1,
#            pageSize=100,
#            date = int(round(datetime.datetime.now().timestamp() * 1000))
#        )
#        resp = requests.get(url=url, params=params)
#        data = resp.json() # Check the JSON Response Content documentation below
#        keycard_list = KeyCard.objects.none()
#        keycard_numbers = []
#        for keycard_json in data['list']:
#            keycard_numbers.append(keycard_json['cardNumber'])
#        keycard_list = KeyCard.objects.filter(bluetooth__in = keycard_numbers)
#        return keycard_list
#
#    def css_charge(self):
#        try:
#            if get_int(self.charge_cache) > 90:
#                return "fa-battery-full perc-100"
#            if get_int(self.charge_cache) > 75:
#                return "fa-battery-three-quarters perc-75"
#            if get_int(self.charge_cache) > 50:
#                return "fa-battery-half perc-50"
#            if get_int(self.charge_cache) > 25:
#                return "fa-battery-quarter perc-25"
#        except: pass
#        return "fa-battery-empty perc-0"
#
#    class Meta:
#        verbose_name = _('Lock')

class Room(models.Model):
    order = models.IntegerField(verbose_name=_('Order'), default=0, null=True)
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    alias = models.CharField(max_length=255, verbose_name=_('Alias'), default="", null=True)
    number = models.CharField(max_length=255, verbose_name=_('Number'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
    lock_group_uuid = models.CharField(max_length=255, verbose_name=_('Lock Group UUID'), default="")
    #parent = models.ForeignKey('self', verbose_name = 'Parent', on_delete=models.SET_NULL, null=True)

    #def childrens(self):
    #    return Room.objects.filter(parent=self)

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

#class KeyCard(models.Model):
#    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
#    bluetooth = models.CharField(max_length=255, verbose_name=_('Bluetooth Code'), default="")
#    cardreader = models.CharField(max_length=255, verbose_name=_('Card Reader Code'), default="")
#    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
#    lock = models.ForeignKey(Lock, verbose_name = _('Lock'), on_delete=models.CASCADE, null=True)
#
#class LockUser(models.Model):
#    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
#    lock_username = models.CharField(max_length=255, verbose_name=_('Lock Username'), default="")
#    lock_password = models.CharField(max_length=255, verbose_name=_('Lock Password'), default="")
#    username = models.CharField(max_length=255, verbose_name=_('Username'), default="")
#    password = models.CharField(max_length=255, verbose_name=_('Password'), default="")
#    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
#
#    @property
#    def project(self):
#        try:
#            return Project.objects.get(uuid=self.project_uuid)
#        except Exception as e:
#            return None
#
#    def create_lock_user(self):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.register_user(self.username, self.lock_password)
#
#    def delete_lock_user(self):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.delete_user(self.lock_username)
#
#    @staticmethod
#    def list_user_not_assigned(project):
#        obj = ShLock(project.lock_access_token)
#        user_list = obj.list_user()
#        result = []
#        for user in user_list:
#            val = LockUser.objects.filter(lock_username=user["username"]).count()
#            if val == 0:
#                result.append(user)
#        return result
#
#    @staticmethod
#    def delete_user_by_username(username):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.delete_user(username)
#
#    class Meta:
#        verbose_name = _('Lock')
#
#class LockGroup(models.Model):
#    order = models.IntegerField(verbose_name=_('Order'), default=0, null=True)
#    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
#    name = models.CharField(max_length=255, verbose_name=_('Alias'), default="", null=True)
#    remote_id = models.CharField(max_length=10, verbose_name=_('Room'), default="")
#    remote_name = models.CharField(max_length=255, verbose_name=_('Remote Name'), default="")
#    project_uuid = models.CharField(max_length = 255, verbose_name= _('Project UUID'), default='')
#
#    @property
#    def project(self):
#        try:
#            return Project.objects.get(uuid=self.project_uuid)
#        except:
#            return None
#
#    def create_lock_group(self):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.add_group(self.remote_name)
#
#    def delete_lock_group(self):
#        obj = ShLock(self.project.lock_access_token)
#        return obj.delete_group(self.remote_id)
#
#    @staticmethod
#    def list_group_not_assigned(access_token):
#        obj = ShLock(access_token)
#        group_list = obj.list_group()
#        result = []
#        for group in group_list:
#            val = LockGroup.objects.filter(remote_name=group["groupName"]).count()
#            if val == 0:
#                result.append(group)
#        return result
#
#    @staticmethod
#    def delete_group_by_id(group_id, project):
#        obj = ShLock(project.lock_access_token)
#        return obj.delete_group(group_id)
#
#    class Meta:
#        verbose_name = _('Lock group')
#        ordering = ["order"]
#
#class LockEkey(models.Model):
#    token = models.CharField(max_length = 32, verbose_name=_('Token'), default="")
#    username = models.CharField(max_length = 255, verbose_name= _('Username'), default='')
#    key_name= models.CharField(max_length = 255, verbose_name= _('Key name'), default='')
#    ekey_id = models.CharField(max_length = 10, verbose_name= _('Ekey id'), default='')
#    lock_uuid = models.CharField(max_length = 255, verbose_name= _('lock UUID'), default='')
#
#    ini_date = models.DateTimeField(verbose_name=_('Ini date'), default=datetime.datetime.now, null=True)
#    end_date = models.DateTimeField(verbose_name=_('End date'), default=datetime.datetime.now, null=True)
#
#    @property
#    def lock(self):
#        try:
#            return Lock.objects.get(uuid=self.lock_uuid)
#        except:
#            return None
#
#class SensiboDevice(models.Model):
#    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
#    name = models.CharField(max_length=255, verbose_name=_('Name'), default="")
#    room = models.CharField(max_length=255, verbose_name=_('Room'), default="")
#    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
#
#    @property
#    def project(self):
#        try:
#            return Project.objects.get(uuid=self.project_uuid)
#        except Exception as e:
#            return None

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

class Module(models.Model):
    code = models.CharField(max_length = 255, verbose_name= _('Code'), default='')
    name = models.CharField(max_length = 255, verbose_name= _('Name'), default='')
    desc = models.TextField(verbose_name= _('Description'), default='')

    class Meta:
        verbose_name = _('Module')

