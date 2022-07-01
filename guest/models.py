from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User

from padword.commons import show_exc
from web.models import Channel, Project

import datetime

class Guest(models.Model):
#     channel = models.ForeignKey('web.Channel', to_field='uuid', on_delete=models.SET_NULL, null=True)
#     project = models.ForeignKey('web.Project', to_field='uuid', on_delete=models.SET_NULL, null=True)
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

    def get_code(self):
        if self.email != None and self.email != "" and "@" in self.email:
            return self.email
        if self.mobile != None and self.mobile != "":
            return self.mobile
        if self.uuid != None and self.uuid != "":
            return self.uuid
        return ""

    def have_valid_booking(self):
        date = timezone.now()
        return (self.check_in <= date and self.check_out >= date) 

    def check_all_notifications(self):
        guest_notifications = [item.notification.id for item in self.notifications.all()]
        notification_list = Notification.objects.filter(project_uuid=self.project_id, all_users=True).exclude(id__in=guest_notifications)
        for notification in notification_list:
            GuestNotification.objects.create(guest=self, notification=notification)
        return True
        
    def get_not_read_notifications(self):
        ll = self.notifications.all()
        for l in ll:
            print("{}: {} - {}".format(l.notification.msg, l.read, l.notification.public))
        return self.notifications.filter(read=False, notification__public=True).count()

    def get_public_notifications(self):
        return self.notifications.filter(notification__public=True)

    #def get_messages(self, guest_access, sender=None, date=""):
    def get_messages(self, guest_access):
        kwargs = {'guest': self}
        #if date != "":
        #    kwargs["date__gt"] = date

        if guest_access: 
            message_list = Message.objects.filter(**kwargs).filter(guest_msg=False).update(guest_read=True)
        else:
            message_list = Message.objects.filter(**kwargs).filter(guest_msg=True).update(sender_read=True)

        return Message.objects.filter(**kwargs)

    def get_locks_id(self):
        return [key.lock for key in self.keys.all()]

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
        date = datetime.datetime.now()
        if room != "":
            return Guest.objects.filter(Q(mobile=code) | Q(email=code)).filter(project_id=project, room=room, check_in__lte=date, check_out__gte=date).first()
        return Guest.objects.filter(Q(mobile=code) | Q(email=code)).filter(project_id=project, check_in__lte=date, check_out__gte=date).first()

    @staticmethod
    def rooms_assigned(project):
        date = datetime.datetime.now()
        return Guest.objects.filter(project_id=project, check_in__lte=date, check_out__gte=date)
               
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

class Key(models.Model):
    lock  = models.CharField(max_length=255, verbose_name='Lock', default="")
    guest = models.ForeignKey(Guest, verbose_name=_("Guest"), on_delete=models.CASCADE, blank=True, null=True, related_name="keys")

    class Meta:
        verbose_name = _("Key")
        verbose_name_plural = _("Keys")

