from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User

from padword.commons import show_exc
from web.models import Channel, Project, Lock, Room
from sensibo.models import SensiboDevice as AdminSensiboDevice

import datetime, pytz


class Guest(models.Model):
    PID = models.IntegerField(verbose_name='PID', default=0)
    UUID = models.CharField(max_length=255, verbose_name='UUID', default="")
    room = models.CharField(max_length=255, verbose_name='Room', default="")
    name = models.CharField(max_length=255, verbose_name='Name', default="")
    surname = models.CharField(max_length=255, verbose_name='Surname', default="")
    referral = models.CharField(max_length=255, verbose_name='Referral', null=True)
    guest_type = models.CharField(max_length=255, verbose_name='Guest Type', default="guest")
    project_id = models.CharField(max_length=255, verbose_name='Project', default="")
    language = models.CharField(max_length=255, verbose_name='Language', default="")
    birthdate = models.DateField(verbose_name='Birthdate', default=datetime.date.today)
    check_in = models.DateTimeField(verbose_name='Check-In', default=datetime.datetime.now)
    check_out = models.DateTimeField(verbose_name='Check-Out', default=datetime.datetime.now)
    language = models.CharField(max_length=255, verbose_name='Language', default="es")
    country = models.CharField(max_length=255, verbose_name='Country', default="es")
    pin = models.CharField(max_length=255, verbose_name='PIN', default="0000000")
    married = models.IntegerField(verbose_name='Married', default=0)
    with_kids = models.IntegerField(verbose_name='With kids', default=0)
    adults = models.IntegerField(verbose_name='Adults', default=0)
    children = models.IntegerField(verbose_name='Childrens', default=0)
    babies = models.IntegerField(verbose_name='Babies', default=0)
    mobile = models.CharField(max_length=255, verbose_name='Mobile', default="")
    email = models.CharField(max_length=255, verbose_name='Email', default="", blank=True)
    balance = models.FloatField(verbose_name='Balance', default=0.)
    deleted = models.IntegerField(verbose_name='Deleted', default=0)
    ext_id = models.CharField(max_length=255, verbose_name='External ID', default="", blank=True, null=True)

    @property
    def project(self):
        try:
            return Project.objects.get(uuid = self.project_id)
        except Exception as e:
            return Project(name='UNKNOWN')

    @property
    def channels(self):
        try:
            channels_uuid = GuestByChannel.objects.filter(UUID = self.UUID).values_list('channel_id', flat=True)
            items = Channel.objects.none()
            for uuid in channels_uuid:
                items = items.union(Channel.objects.filter(uuid=uuid))
            return (items)
        except Exception as e:
            print (show_exc(e))
            return Channel.objects.none()

    @property
    def room_obj(self):
        try:
            return Room.objects.filter(project_uuid=self.project_id, number=self.room).first()
        except Exception as e:
            return Project(name='UNKNOWN')

    @property
    def check_in_gmt(self):
        return self.project.gmt_date(self.check_in)

    @property
    def check_out_gmt(self):
        return self.project.gmt_date(self.check_out)

    @property
    def regime(self):
        try:
            return self.regimes.first().regime
        except:
            return None

    @property
    def pwa_link(self):
        try:
            return "{}{}".format(settings.MAIN_URL, reverse("guest-access-auto", kwargs = {'guest_uuid': self.UUID}))
        except:
            return reverse("guest-access-auto", kwargs = {'guest_uuid': self.UUID})

    def get_code(self):
        if self.email != None and self.email != "" and "@" in self.email:
            return self.email
        if self.mobile != None and self.mobile != "":
            return self.mobile
        if self.uuid != None and self.uuid != "":
            return self.uuid
        return ""

    def have_valid_booking(self):
        #date = timezone.now()
        date = pytz.utc.localize(datetime.datetime.now() + datetime.timedelta(hours=1))
        return (self.check_in <= date and self.check_out >= date) 

    def check_all_notifications(self):
        guest_notifications = [item.notification.id for item in self.notifications.all()]
        notification_list = Notification.objects.filter(project_uuid=self.project_id, all_users=True).exclude(id__in=guest_notifications)
        for notification in notification_list:
            GuestNotification.objects.create(guest=self, notification=notification)
        return True
        
    def get_not_read_notifications(self):
        limit = datetime.datetime.now() + datetime.timedelta(days=-7)
        return self.notifications.filter(read=False, notification__public=True, notification__date__gte=limit).count()

    def get_public_notifications(self):
        limit = datetime.datetime.now() + datetime.timedelta(days=-7)
        return self.notifications.filter(notification__public=True, notification__date__gte=limit).order_by('-notification__date')

    def get_messages(self, guest_access):
        kwargs = {'guest': self}

        if guest_access: 
            message_list = Message.objects.filter(**kwargs).filter(guest_msg=False).update(guest_read=True)
        else:
            message_list = Message.objects.filter(**kwargs).filter(guest_msg=True).update(sender_read=True)

        return Message.objects.filter(**kwargs)

    '''
        Locks
    '''
    def get_locks(self):
        #return Lock.objects.filter(Q(room=self.room) | Q(room="*")).filter(project_uuid=self.project_id).order_by("-room") if self.room != "" else []
        if self.room == "":
            return []
        items = Lock.objects.none()
        room_list = Lock.objects.filter(room=self.room, project_uuid=self.project_id).order_by("-room")
        global_list = Lock.objects.filter(room="*", group_uuid="", project_uuid=self.project_id).order_by("-room")
        #global_list = Lock.objects.filter(room="*", project_uuid=self.project_id).order_by("-room")
        group_uuid_list = [lock.group_uuid for lock in room_list]
        group_list = Lock.objects.filter(room="*", group_uuid__in=group_uuid_list, project_uuid=self.project_id).order_by("-room")
        return items.union(room_list).union(global_list).union(group_list)

    def get_locks_json(self):
        #lock_list = Lock.objects.filter(Q(room=self.room) | Q(room="*")).filter(project_uuid=self.project_id).order_by("-room") if self.room != "" else []
        lock_list = self.get_locks()
        dic = {}
        for lock in lock_list:
            dic["uuid"] = lock.uuid
            dic["alias"] = lock.alias
            dic["codes"] = []
            for code in self.keycodes.filter(lock=lock):
                dic["codes"].append(code.code)
            dic["cards"] = []
            for card in self.keycards.filter(lock=lock):
                dic["cards"].append(card.code)
        return dic

    def add_key_code(self, lock, code=""):
        code = self.mobile_to_code() if code == "" else code
        #code_id = lock.set_code(code, self.check_in, self.check_out, "{} {}".format(self.name, self.surname))
        #code_id = lock.set_code(code, self.get_start_date(), self.check_out, "{} {}".format(self.name, self.surname))
        code_id = lock.set_code(code, self.check_in_gmt, self.check_out_gmt, "{} {}".format(self.name, self.surname))
        if not "Error" in str(code_id):
            key = KeyCode.objects.create(lock = lock, guest = self, code = code, code_id = code_id)
        elif "passcode" in str(code_id) and "already exists" in str(code_id):
            for passcode in lock.get_all_passcodes():
                if passcode.get("keyboardPwd") == code:
                    key = KeyCode.objects.create(lock = lock, guest = self, code = code, code_id = passcode.get("keyboardPwdId"))
        else:
            key = KeyCode.objects.create(lock = lock, guest = self)
            return code_id
        return ""

    def add_all_key_code(self, code=""):
        err = ""
        for lock in self.get_locks():
            error = self.add_key_code(lock, code)
            if error != "":
                err = "{}<br/>{}: {}".format(err, lock.alias, error) if err != "" else "{}: {}".format(lock.alias, error)
        return err

    def change_all_key_code(self, code):
        self.remove_all_key_codes()
        err = self.add_all_key_code(code)
        return err

    def change_all_key_code_date(self):
        err = ""
        for key in self.keycodes.all():
            #start_date = key.guest.check_in - datetime.timedelta(hours=1)
            #errcode = key.lock.change_code(key.code_id, key.code, start_date, key.guest.check_out)
            #errcode = key.lock.change_code(key.code_id, key.code, key.guest.get_start_date(), key.guest.check_out)
            error = key.lock.change_code(key.code_id, key.code, key.guest.check_in_gmt, key.guest.check_out_gmt)
            if error != "":
                err = "{}<br/>{}: {}".format(err, key.lock.alias, error) if err != "" else "{}: {}".format(key.lock.alias, error)
        return err

    def remove_all_key_codes(self):
        for key in self.keycodes.all():
            errcode = key.lock.remove_code(key.code_id)
            if errcode == 0:
                key.delete()

    def remove_all_key_codes_log(self):
        msg = ""
        for key in self.keycodes.all():
            msg += "<br/> -> Remove code {} from key {}".format(key.code, key.lock.alias)
            errcode = key.lock.remove_code(key.code_id)
            msg += "<br/> --> {}".format(errcode)
            if errcode == 0:
                key.delete()
        return msg

    def add_all_key_card(self, code):
        for lock in self.get_locks():
            #errcode = lock.add_card(code, self.check_in, self.check_out)
            #errcode = lock.add_card(code, self.get_start_date(), self.check_out)
            errcode = lock.add_card(code, self.check_in_gmt, self.check_out_gmt)
            if not "Error" in str(errcode):
                KeyCard.objects.create(code=code, card_id=errcode, lock=lock, guest=self)

    def change_all_key_card_date(self):
        err = ""
        for key in self.keycards.all():
            #start_date = key.guest.check_in - datetime.timedelta(hours=1)
            #errcode = key.lock.change_period_card(key.card_id, start_date, key.guest.check_out)
            #errcode = key.lock.change_period_card(key.card_id, key.guest.get_start_date(), key.guest.check_out)
            error = key.lock.change_period_card(key.card_id, key.guest.check_in_gmt, key.guest.check_out_gmt)
            if error != "":
                err = "{}<br/>{}: {}".format(err, key.lock.alias, error) if err != "" else "{}: {}".format(key.lock.alias, error)
        return err

    def remove_all_key_cards(self, code=""):
        key_list = self.keycards.filter(code=code) if code != "" else self.keycards.all()
        for key in key_list:
            errcode = key.lock.remove_card(key.card_id)
            if errcode == 0:
                key.delete()

    def remove_all_key_cards_log(self, code=""):
        key_list = self.keycards.filter(code=code) if code != "" else self.keycards.all()
        msg = ""
        for key in key_list:
            msg += "<br/> -> Remove card code {} from key {}".format(key.code, key.lock.alias)
            errcode = key.lock.remove_card(key.card_id)
            msg += "<br/> --> {}".format(errcode)
            if errcode == 0:
                key.delete()
        return msg

    def change_room(self, new_room=""):
        current_code = self.keycodes.first()
        card_list = list(self.keycards.all().values_list('code', flat=True).distinct())
        self.remove_all_key_codes()
        self.remove_all_key_cards()
        self.room = new_room
        self.save()
        err = ""
        if current_code != None:
            err += self.add_all_key_code(current_code.code)
        else:
            err += self.add_all_key_code()

        for code in card_list:
            self.add_all_key_card(code)
        return err

    def can_open_lock(self, lock):
        return ((self.room == lock.room) or (lock.room == "*"))

    def mobile_to_code(self):
        try:
            return self.mobile.rstrip()[-4:]
        except:
            return ""

    '''
        Sensibo
    '''
    def remove_all_sensibo_devices(self):
        for dev in self.sensibo_devices.all():
            dev.delete()

    def change_sensibo_devices(self, new_room):
        self.remove_all_sensibo_devices()
        dev_list = AdminSensiboDevice.objects.filter(room=new_room)
        for dev in dev_list:
            SensiboDevice.objects.create(guest=self, uuid=dev.uuid, name=dev.name)

    '''
        Statics
    '''
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

    @classmethod
    def by_channel(cls, channels):
        try:
            items = GuestByChannel.objects.none()
            if isinstance(channels, models.query.QuerySet):
                for channel_uuid in channels.all().values_list('uuid', flat=True):
                    items = items.union(GuestByChannel.objects.filter(channel_id = channel_uuid))
            else:
                items = GuestByChannel.objects.filter(channel_id = channels.uuid)
            items = Guest.objects.filter(UUID__in = items.all().values_list('UUID', flat=True))
            return items
        except Exception as e:
            print (show_exc(e))
            return Guest.objects.none()
       
    @staticmethod
    def current_by_room_project(room, project):
        date = datetime.datetime.now()
        return Guest.objects.filter(room=room, project_id=project, check_in__lte=date, check_out__gte=date)

    @staticmethod
    def check_valid_booking(project, code, room=""):
        #date = datetime.datetime.now()
        date = datetime.datetime.now() + datetime.timedelta(hours=1)
        if room != "":
            return Guest.objects.filter(Q(mobile=code) | Q(email=code)).filter(project_id=project, room=room, check_in__lte=date, check_out__gte=date).first()
        return Guest.objects.filter(Q(mobile=code) | Q(email=code)).filter(project_id=project, check_in__lte=date, check_out__gte=date).first()

    @staticmethod
    def rooms_assigned(project):
        date = datetime.datetime.now()
        return Guest.objects.filter(project_id=project, check_in__lte=date, check_out__gte=date)
               
    def delete_all(self):
        self.remove_all_key_codes()
        self.remove_all_key_cards()
        self.remove_all_sensibo_devices()
        self.delete()

    def delete_soft(self):
        msg = self.remove_all_key_codes_log()
        msg += self.remove_all_key_cards_log()
        self.remove_all_sensibo_devices()
        self.deleted = 1
        self.save()
        return msg

    class Meta:
        if len (settings.DATABASES) > 1:
            managed = False
            db_table = 'guests'
        ordering = ('project_id', '-check_in', '-check_out')
        verbose_name = _('Guest')

class GuestReferral(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'), default="", unique=True, null=False, blank=False)
    code = models.IntegerField(verbose_name=_('Code'), unique=True)
    created_at = models.DateTimeField(verbose_name=_('Created at'), default=datetime.datetime.now)
    updated_at = models.DateTimeField(verbose_name=_('Updated at'), default=datetime.datetime.now)

    class Meta:
        if len (settings.DATABASES) > 1:
            managed = False
            db_table = 'guest_referrals'
        ordering = ('name', 'created_at', 'updated_at')
        verbose_name = _('Guest')

class GuestByChannel(models.Model):
#     channel = models.ForeignKey('web.Channel', to_field='uuid', on_delete=models.SET_NULL, null=True)
#     project = models.ForeignKey('web.Project', to_field='uuid', on_delete=models.SET_NULL, null=True)
    PID = models.IntegerField(verbose_name='PID')
    UUID = models.CharField(max_length=255, verbose_name='UUID')
    room = models.CharField(max_length=255, verbose_name='Room')
    name = models.CharField(max_length=255, verbose_name='Name')
    surname = models.CharField(max_length=255, verbose_name='Surname')
    project_id = models.CharField(max_length=255, verbose_name='Project')
    channel_id = models.CharField(max_length=255, verbose_name='Channel')
    language = models.CharField(max_length=255, verbose_name='Language')
    check_in = models.DateTimeField(verbose_name='Check-In')
    check_out = models.DateTimeField(verbose_name='Check-Out')
    referral = models.CharField(max_length=255, verbose_name='Referral', default="")
    guest_type = models.CharField(max_length=255, verbose_name='Guest Type', default="guest")
    birthdate = models.DateField(verbose_name='Birthdate', default=datetime.date.today)
    country = models.CharField(max_length=255, verbose_name='Country', default="es")
    pin = models.CharField(max_length=255, verbose_name='PIN', default="0000000")
    married = models.IntegerField(verbose_name='Married', default=0)
    with_kids = models.IntegerField(verbose_name='With kids', default=0)
    adults = models.IntegerField(verbose_name='Adults', default=0)
    children = models.IntegerField(verbose_name='Childrens', default=0)
    babies = models.IntegerField(verbose_name='Babies', default=0)
    mobile = models.CharField(max_length=255, verbose_name='Mobile', default="")
    email = models.CharField(max_length=255, verbose_name='Email', default="")
    balance = models.FloatField(verbose_name='Balance', default=0.)
    deleted = models.IntegerField(verbose_name='Deleted', default=0)

    @property
    def project(self):
        try:
            return Project.objects.get(uuid = self.project_id)
        except Exception as e:
            return Project(name='UNKNOWN')

    @property
    def channel(self):
        try:
            return Channel.objects.get(uuid = self.channel_id)
        except Exception as e:
            return Channel(name='UNKNOWN')

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

    @classmethod
    def by_channel(cls, channels):
        try:
            items = Guest.objects.none()
            if isinstance(channels, models.query.QuerySet):
                for channel_uuid in channels.all().values_list('uuid', flat=True):
                    items = items.union(Guest.objects.filter(channel_id = channel_uuid))
            else:
                items = Guest.objects.filter(channel_id = channels.uuid)
            return items
        except Exception as e:
            print (show_exc(e))
            return Guest.objects.none()
        

    class Meta:
        if len (settings.DATABASES) > 1:
            managed = False
            db_table = 'guests-by-channel'
        verbose_name = _('Guest')


class Notification(models.Model):
    all_users = models.BooleanField(verbose_name=_("All users"), default=False)
    public = models.BooleanField(verbose_name=_("Public"), default=False)
    date = models.DateTimeField(verbose_name='Date', default=datetime.datetime.now)
    subject = models.CharField(max_length=600, verbose_name=_('Subject'), default="")
    msg = models.TextField(verbose_name=_("Message"), default="", blank=True)
    project_uuid = models.CharField(max_length=255, verbose_name='Project', default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid = self.project_uuid)
        except Exception as e:
            return Project(name='UNKNOWN')

    class Meta:
        verbose_name = _('Notification')
        ordering = ('-date',)

class GuestNotification(models.Model):
    read = models.BooleanField(verbose_name=_("Read"), default = False)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, verbose_name=_("Guest"), related_name="notifications")
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, verbose_name=_("Notification"), related_name="guests", null=True)

    class Meta:
        verbose_name = _('Guest notification')

class Message(models.Model):
    guest_read = models.BooleanField(verbose_name=_('Guest Readed'), default=False)
    sender_read = models.BooleanField(verbose_name=_('Sender Readed'), default=False)
    guest_msg = models.BooleanField(verbose_name=_('Guest Message'), default=False)
    date = models.DateTimeField('date', auto_now_add=True)
    msg = models.TextField(verbose_name=_("Message"), default="", blank=True)
    guest = models.ForeignKey(Guest, verbose_name=_("Guest"), on_delete=models.CASCADE, blank=True, null=True, related_name="messages")
    #sender = models.ForeignKey(User, verbose_name=_("Sender"), on_delete=models.CASCADE, blank=True, null=True, related_name="messages_sent")

    class Meta:
        verbose_name = _("Chat")
        verbose_name_plural = _("Chat")
        ordering = ["date"]

class KeyCode(models.Model):
    code = models.CharField(max_length=100, verbose_name=_('Code'), default="")
    code_id = models.CharField(max_length=100, verbose_name=_('Code Id'), default="")
    lock = models.ForeignKey(Lock, verbose_name=_("Lock"), on_delete=models.CASCADE, blank=True, null=True, related_name="keycodes")
    guest = models.ForeignKey(Guest, verbose_name=_("Guest"), on_delete=models.CASCADE, blank=True, null=True, related_name="keycodes")

    class Meta:
        verbose_name = _("Key")
        verbose_name_plural = _("Keys")

class KeyCard(models.Model):
    code = models.CharField(max_length=100, verbose_name=_('Code'), default="")
    card_id = models.CharField(max_length=100, verbose_name=_('Card Id'), default="")
    lock = models.ForeignKey(Lock, verbose_name=_("Lock"), on_delete=models.CASCADE, blank=True, null=True, related_name="keycards")
    guest = models.ForeignKey(Guest, verbose_name=_("Guest"), on_delete=models.CASCADE, blank=True, null=True, related_name="keycards")

    class Meta:
        verbose_name = _("Key")
        verbose_name_plural = _("Keys")

class SensiboDevice(models.Model):
    uuid = models.CharField(max_length=200, verbose_name=_('UUID'), default="")
    name = models.CharField(max_length=255, verbose_name=_('Name'), default="")
    start_time = models.CharField(max_length=20, verbose_name=_('Start Time'), default="")
    mode = models.CharField(max_length=20, verbose_name=_('Mode'), default="")
    temp = models.CharField(max_length=20, verbose_name=_('Temp'), default="")
    level = models.CharField(max_length=20, verbose_name=_('Level'), default="")
    guest = models.ForeignKey(Guest, verbose_name=_("Guest"), on_delete=models.CASCADE, blank=True, null=True, related_name="sensibo_devices")

    class Meta:
        verbose_name = _("Sensibo device")
        verbose_name_plural = _("Sensibo devices")

class Wristband(models.Model):
    code = models.CharField(max_length=255, verbose_name=_('Code'), default="")
    guest = models.ForeignKey(Guest, verbose_name=_("Guest"), on_delete=models.CASCADE, blank=True, null=True, related_name="bands")

    class Meta:
        verbose_name = _("Wristband")
        verbose_name_plural = _("Wristbands")

'''
    Regime
'''
class Regime(models.Model):
    code = models.CharField(max_length=50, verbose_name='Code', default="")
    name = models.CharField(max_length=255, verbose_name='Name', default="")

    class Meta:
        verbose_name = _('Regime')

class ProjectRegime(models.Model):
    regime = models.ForeignKey(Regime, on_delete=models.CASCADE, verbose_name=_("Regime"), related_name="projects")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name=_("Project"), related_name="regimes")

class GuestRegime(models.Model):
    regime = models.ForeignKey(Regime, on_delete=models.CASCADE, verbose_name=_("Regime"), related_name="guests")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, verbose_name=_("Guest"), related_name="regimes")


