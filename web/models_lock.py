from django.db import models
from django.utils.translation import ugettext as _

from padword.commons import get_int
from .lock_lib import ShLock
from .models import Project, Room

import datetime, pytz
import requests


class Lock(models.Model):
    private = models.BooleanField(verbose_name=_('Private'), default=False)
    box = models.BooleanField(verbose_name=_('Deposit box'), default=False)
    last_update = models.DateTimeField(verbose_name=_('Last update'), default=datetime.datetime.now, null=True)
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    alias = models.CharField(max_length=255, verbose_name=_('Alias'), default="", null=True)
    room = models.CharField(max_length=255, verbose_name=_('Room'), default="")
    charge_cache = models.CharField(max_length=10, verbose_name=_('Charge cache'), default="")
    state_cache = models.CharField(max_length=100, verbose_name=_('State cache'), default="")
    gateway_cache = models.CharField(max_length=900, verbose_name=_('Gateway cache'), default="")
    wifi_cache = models.CharField(max_length=900, verbose_name=_('Wifi cache'), default="")
    #code_cache = models.CharField(max_length=900, verbose_name=_('Code cache'), default="")
    #card_cache = models.CharField(max_length=1900, verbose_name=_('Card cache'), default="")
    code_cache = models.TextField(verbose_name=_('Code cache'), default="")
    card_cache = models.TextField(verbose_name=_('Card cache'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
    group_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except Exception as e:
            return None

    @property
    def group(self):
        try:
            return LockGroup.objects.get(uuid=self.group_uuid)
        except Exception as e:
            return None

    @property
    def room_obj(self):
        return Room.objects.filter(project_uuid=self.project_uuid, number=self.room).first()

    @property
    def state(self):
        now = pytz.utc.localize(datetime.datetime.now())
        if ((now - self.last_update).seconds/60) > 15:
            self.update_params()
        return _("unlock") if get_int(self.state_cache) != 0 else _("lock")

    @property
    def charge(self):
        now = pytz.utc.localize(datetime.datetime.now())
        if ((now - self.last_update).seconds/60) > 15:
            self.update_params()
        return self.charge_cache

    @property
    def gateway(self):
        now = pytz.utc.localize(datetime.datetime.now())
        if ((now - self.last_update).seconds/60) > 15:
            self.update_params()
        return self.gateway_cache

    @property
    def wifi(self):
        now = pytz.utc.localize(datetime.datetime.now())
        if ((now - self.last_update).seconds/60) > 15:
            self.update_params()
        return self.wifi_cache

    def update_params(self):
        #t1 = datetime.datetime.now()
        obj = ShLock(self.project.lock_access_token)
        #t2 = datetime.datetime.now()

        #state_cache = obj.get_lock_state(self.uuid)
        #t3 = datetime.datetime.now()
        charge_cache = obj.get_lock_charge(self.uuid)
        #t4 = datetime.datetime.now()
        gateway_cache = obj.get_lock_gateway(self.uuid)
        #t5 = datetime.datetime.now()
        wifi_cache = obj.get_lock_wifi(self.uuid)
        #t6 = datetime.datetime.now()
        code_cache = self.get_all_passcodes_cache()
        card_cache = self.get_all_cards_cache()

        #self.state_cache = state_cache if "Error" not in str(state_cache) else ""
        self.state_cache = ""
        self.charge_cache = charge_cache if "Error" not in str(charge_cache) else ""
        #self.gateway_cache = _("Connected") if len(gateway_cache["list"]) > 0 else _("Not connected")
        self.gateway_cache = gateway_cache
        self.wifi_cache = wifi_cache if "Error" not in str(wifi_cache) else ""
        self.last_update = pytz.utc.localize(datetime.datetime.now())
        self.code_cache = code_cache
        self.save()
        #t7 = datetime.datetime.now()
        #print("START: {}".format(t1))
        #print("T2: {}".format(t2-t1))
        #print("STATE: {}".format(t3-t2))
        #print("CHARGE: {} {}".format(charge_cache, t4-t3))
        #print("GATEWAY:{} {}".format(gateway_cache, t5-t4))
        #print("WIFI:{} {}".format(wifi_cache, t6-t5))
        #print("END: {}".format(t7-t6))
        #print("TOTAL: {}".format(t7-t1))

    def open_lock(self):
        sh_lock = ShLock(self.project.lock_access_token)
        return sh_lock.open_lock_by_id(self.uuid)

    def set_code(self, code, start_date, end_date, name=""):
        obj = ShLock(self.project.lock_access_token)
        code_name = name if name != "" else self.alias
        lock =  obj.set_lock_code(self.uuid, code, code_name, start_date, end_date)
        if "Error" not in str(lock) and code_name not in self.code_cache:
            self.code_cache += ",{}".format(code)
            self.save()
        return lock

    def get_code(self, code_type, start_date, end_date, name=""):
        obj = ShLock(self.project.lock_access_token)
        return obj.get_lock_code(self.uuid, code_type, start_date, end_date, name)

    def change_code(self, code_id, new_code, start_date, end_date):
        obj = ShLock(self.project.lock_access_token)
        return obj.change_lock_code(self.uuid, code_id, new_code, start_date, end_date)

    def remove_code(self, code_id, code=""):
        key_code_list = self.keycodes.filter(code_id=code_id)
        for key_code in key_code_list:
            key_code.delete()
        obj = ShLock(self.project.lock_access_token)
        lock = obj.remove_lock_code(self.uuid, code_id)
        if "Error" not in str(lock) and code != "" and code in self.code_cache:
            self.code_cache = self.code_cache.replace(",{}".format(code), "").replace(code, "")
            self.save()
        return lock

    def get_all_passcodes(self):
        obj = ShLock(self.project.lock_access_token)
        return obj.get_lock_all_passcodes(self.uuid)

    def get_all_passcodes_cache(self):
        codes_cache = ""
        obj = ShLock(self.project.lock_access_token)
        codes = obj.get_lock_all_passcodes(self.uuid)
        if "Error" not in str(codes):
            for code in codes:
                codes_cache += "{},".format(code.get("keyboardPwd"))
        return codes_cache[:-1] if len(codes_cache) > 0 else codes_cache

    def add_card(self, card_number, start_date, end_date, name=""):
        obj = ShLock(self.project.lock_access_token)
        card_name = name if name != "" else self.alias
        lock = obj.lock_add_card(self.uuid, card_number, card_name, start_date, end_date)
        if "Error" not in str(lock) and card_name not in self.card_cache:
            self.card_cache += ",{}".format(card_number)
            self.save()
        return lock

    def remove_card(self, code_id, code=""):
        key_card_list = self.keycards.filter(card_id=code_id)
        for key_card in key_card_list:
            key_card.delete()
        obj = ShLock(self.project.lock_access_token)
        lock = obj.remove_lock_card(self.uuid, code_id)
        if "Error" not in str(lock) and str(code) != "" and str(code) in self.card_cache:
            self.card_cache = self.card_cache.replace(",{}".format(code), "").replace(code, "")
            self.save()
        return lock

    def get_all_cards(self):
        obj = ShLock(self.project.lock_access_token)
        return obj.get_lock_all_cards(self.uuid)

    def get_all_cards_cache(self):
        codes_cache = ""
        obj = ShLock(self.project.lock_access_token)
        codes = obj.get_lock_all_cards(self.uuid)
        if "Error" not in str(codes):
            for code in codes:
                codes_cache += "{},".format(code.get("cardNumber"))
        return codes_cache[:-1] if len(codes_cache) > 0 else codes_cache

    def change_period_card(self, card_id, start_date, end_date):
        obj = ShLock(self.project.lock_access_token)
        return obj.change_period_lock_card(self.uuid, card_id, start_date, end_date)

    def set_group(self):
        obj = ShLock(self.project.lock_access_token)
        if self.group != None:
            return obj.set_lock_group(self.uuid, self.group.remote_id)
        else:
            return obj.set_lock_group(self.uuid, "")

    def add_ekey(self, username, key_name, start_date, end_date):
        obj = ShLock(self.project.lock_access_token)
        return obj.send_lock_key(self.uuid, username, key_name, start_date, end_date)

    def remove_ekey(self, ekey_id):
        #key_code_list = self.ekeys.filter(ekey_id=ekey_id)
        #for ekey in ekey_list:
        #    ekey.delete()
        obj = ShLock(self.project.lock_access_token)
        return obj.remove_lock_key(self.uuid, ekey_id)

    def get_all_ekeys(self):
        #obj = ShLock()
        #return obj.get_lock_all_keys(self.uuid)
        return LockEkey.objects.filter(lock_uuid=self.uuid)

    def get_gateway_name_by_id(self, gateway_id):
        obj = ShLock(self.project.lock_access_token)
        return obj.get_gateway_name(self.uuid, gateway_id)

    def get_all_records(self):
        obj = ShLock(self.project.lock_access_token)
        return obj.get_lock_all_records(self.uuid)

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
        try:
            if get_int(self.charge_cache) > 90:
                return "fa-battery-full perc-100"
            if get_int(self.charge_cache) > 75:
                return "fa-battery-three-quarters perc-75"
            if get_int(self.charge_cache) > 50:
                return "fa-battery-half perc-50"
            if get_int(self.charge_cache) > 25:
                return "fa-battery-quarter perc-25"
        except: pass
        return "fa-battery-empty perc-0"

    @staticmethod
    def get_locks_by_room(room):
        return Lock.objects.filter(project_uuid = room.project_uuid, room = room.number).order_by('pk') if room.number != "" else []

    class Meta:
        verbose_name = _('Lock')

class KeyCard(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    bluetooth = models.CharField(max_length=255, verbose_name=_('Bluetooth Code'), default="")
    cardreader = models.CharField(max_length=255, verbose_name=_('Card Reader Code'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
    lock = models.ForeignKey(Lock, verbose_name = _('Lock'), on_delete=models.CASCADE, null=True)

class LockUser(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    lock_username = models.CharField(max_length=255, verbose_name=_('Lock Username'), default="")
    lock_password = models.CharField(max_length=255, verbose_name=_('Lock Password'), default="")
    username = models.CharField(max_length=255, verbose_name=_('Username'), default="")
    password = models.CharField(max_length=255, verbose_name=_('Password'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except Exception as e:
            return None

    def create_lock_user(self):
        obj = ShLock(self.project.lock_access_token)
        return obj.register_user(self.username, self.lock_password)

    def delete_lock_user(self):
        obj = ShLock(self.project.lock_access_token)
        return obj.delete_user(self.lock_username)

    @staticmethod
    def list_user_not_assigned(project):
        obj = ShLock(project.lock_access_token)
        user_list = obj.list_user()
        result = []
        for user in user_list:
            val = LockUser.objects.filter(lock_username=user["username"]).count()
            if val == 0:
                result.append(user)
        return result

    @staticmethod
    def delete_user_by_username(username):
        obj = ShLock(self.project.lock_access_token)
        return obj.delete_user(username)

    class Meta:
        verbose_name = _('Lock')

class LockGroup(models.Model):
    order = models.IntegerField(verbose_name=_('Order'), default=0, null=True)
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    name = models.CharField(max_length=255, verbose_name=_('Alias'), default="", null=True)
    remote_id = models.CharField(max_length=10, verbose_name=_('Room'), default="")
    remote_name = models.CharField(max_length=255, verbose_name=_('Remote Name'), default="")
    project_uuid = models.CharField(max_length = 255, verbose_name= _('Project UUID'), default='')

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

    def create_lock_group(self):
        obj = ShLock(self.project.lock_access_token)
        return obj.add_group(self.remote_name)

    def delete_lock_group(self):
        obj = ShLock(self.project.lock_access_token)
        return obj.delete_group(self.remote_id)

    @staticmethod
    def list_group_not_assigned(access_token):
        obj = ShLock(access_token)
        group_list = obj.list_group()
        result = []
        for group in group_list:
            val = LockGroup.objects.filter(remote_name=group["groupName"]).count()
            if val == 0:
                result.append(group)
        return result

    @staticmethod
    def delete_group_by_id(group_id, project):
        obj = ShLock(project.lock_access_token)
        return obj.delete_group(group_id)

    class Meta:
        verbose_name = _('Lock group')
        ordering = ["order"]

class LockEkey(models.Model):
    token = models.CharField(max_length = 32, verbose_name=_('Token'), default="")
    username = models.CharField(max_length = 255, verbose_name= _('Username'), default='')
    key_name= models.CharField(max_length = 255, verbose_name= _('Key name'), default='')
    ekey_id = models.CharField(max_length = 10, verbose_name= _('Ekey id'), default='')
    lock_uuid = models.CharField(max_length = 255, verbose_name= _('lock UUID'), default='')

    ini_date = models.DateTimeField(verbose_name=_('Ini date'), default=datetime.datetime.now, null=True)
    end_date = models.DateTimeField(verbose_name=_('End date'), default=datetime.datetime.now, null=True)

    @property
    def lock(self):
        try:
            return Lock.objects.get(uuid=self.lock_uuid)
        except:
            return None

class LockCodeExtId(models.Model):
    code = models.CharField(max_length = 10, verbose_name=_('Code'), default="")
    ext_id = models.CharField(max_length = 10, verbose_name= _('Ekey id'), default='')
    lock_uuid = models.CharField(max_length = 255, verbose_name= _('lock UUID'), default='')
    project_uuid = models.CharField(max_length = 255, verbose_name= _('Project UUID'), default='')

    @property
    def lock(self):
        try:
            return Lock.objects.get(uuid=self.lock_uuid)
        except:
            return None

class LockCron(models.Model):
    done = models.BooleanField(verbose_name=_('Done'), default=False)
    task = models.CharField(max_length = 100, verbose_name=_('Task'), default="")
    lock_list = models.TextField(verbose_name= _('Lock list'), default='')
    params = models.TextField(verbose_name= _('Params'), default='')
    project_uuid = models.CharField(max_length = 255, verbose_name= _('Project UUID'), default='')

    @property
    def lock(self):
        try:
            return Lock.objects.get(uuid=self.lock_uuid)
        except:
            return None

    @property
    def lock_list_html(self):
        lock_list = self.lock_list.split(";")
        result = ""
        for l in lock_list:
            try:
                lock = Lock.objects.get(id=l)
                result = "{}{},".format(result, lock.alias)
            except:
                pass
        return result[:-1]
        #return self.lock_list.split(";")


