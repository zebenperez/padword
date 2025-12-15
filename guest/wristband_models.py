from django.db import models
from django.db.models import Q, Sum
from django.utils.translation import ugettext as _
from django.utils import timezone

from padword.commons import show_exc, new_ui_slug, get_random_digits, reverse_cardkey
from web.models import Project
from .models import Guest

import datetime, pytz, time


class WristbandType(models.Model):
    code = models.CharField(max_length=50, verbose_name=_("Code"), default="", blank=True)
    name = models.CharField(max_length=255, verbose_name=_("Name"), default="", blank=True)

    class Meta:
        verbose_name = _("Wristband type")
        verbose_name_plural = _("Wristbands type")

class Wristband(models.Model):
    kid = models.BooleanField(verbose_name=_("Kid"), default=False)
    locks = models.BooleanField(verbose_name=_("Locks"), default=False)
    code = models.CharField(max_length=255, verbose_name=_('Code'), default="")
    name = models.CharField(max_length=255, verbose_name=_('Name'), default="")
    guest = models.ForeignKey(Guest, verbose_name=_("Guest"), on_delete=models.CASCADE, blank=True, null=True, related_name="bands")
    type = models.ForeignKey(WristbandType, verbose_name=_("Type"), on_delete=models.SET_NULL, blank=True, null=True)

    @property
    def balance(self):
        try:
            return self.balances.aggregate(Sum('amount'))["amount__sum"] if self.balances.count() > 0 else 0
        except Exception as e:
            print(e)
            return -1

    @property
    def is_close(self):
        wb = WristbandBackup.objects.filter(code=self.code, guest_uuid=self.guest.UUID).first()
        return (wb != None)

    def get_or_create_backup(self):
        wb = WristbandBackup.objects.filter(code=self.code, guest_uuid=self.guest.UUID).first()
        if wb == None:
            wb = WristbandBackup.objects.create(code=self.code, guest_uuid=self.guest.UUID)
        return wb

    def can_access_zone(self, zone):
        if self.guest == None:
            return False
        zones = [item.zone for item in self.guest.zones.all()]
        return (zone in zones)

    @staticmethod
    def get_active_by_project(project, code):
        #now = datetime.datetime.now()
        #now = timezone.now()
        now = project.local_date(timezone.now())
        now = now.strftime("%Y-%m-%d %H:%M:%S")
        return Wristband.objects.filter(code=code, guest__project_id=project.uuid, guest__deleted=False, guest__check_in__lte=now, guest__check_out__gte=now).first()

    class Meta:
        verbose_name = _("Wristband")
        verbose_name_plural = _("Wristbands")

class WristbandBalance(models.Model):
    date = models.DateTimeField(verbose_name=_('Date'), default=datetime.datetime.now)
    amount = models.FloatField(verbose_name=_('Amount'), default=0)
    desc = models.TextField(verbose_name=_("Description"), default="", blank=True)
    wristband = models.ForeignKey(Wristband, verbose_name=_("Wristband"), on_delete=models.CASCADE, blank=True, null=True, related_name="balances")

    class Meta:
        verbose_name = _("Wristband balance")
        verbose_name_plural = _("Wristbands balance")

class WristbandLog(models.Model):
    date = models.DateTimeField(verbose_name=_('Date'), default=datetime.datetime.now)
    desc = models.TextField(verbose_name=_("Description"), default="", blank=True)
    wristband = models.ForeignKey(Wristband, verbose_name=_("Wristband"), on_delete=models.CASCADE, blank=True, null=True, related_name="logs")

    class Meta:
        verbose_name = _("Wristband log")
        verbose_name_plural = _("Wristbands log")

class WristbandAccessZone(models.Model):
    default = models.BooleanField(verbose_name=_("Default"), default=False)
    reset_time = models.TimeField(_("Reset Time"), blank=True, default=datetime.time(23, 00))
    uuid = models.CharField(max_length = 255, verbose_name= _('UUID'), default=new_ui_slug)
    name = models.CharField(max_length=255, verbose_name='Name', default="")
    code = models.CharField(max_length=255, verbose_name='Code', default="")
    project_uuid = models.CharField(max_length = 255, verbose_name= _('Project UUID'), default='')

    @property
    def project(self):
        try:
            return Project.objects.get(uuid = self.project_uuid)
        except Exception as e:
            return Project(name='UNKNOWN')

    class Meta:
        verbose_name = _("Wristband Access Zone")
        verbose_name_plural = _("Wristbands Access Zones")
        ordering = ["-id"]

class WristbandAccessZoneTimes(models.Model):
    ini_time = models.TimeField(_("Initial Time"), blank=True, default=datetime.time(8, 00))
    end_time = models.TimeField(_("End Time"), blank=True, default=datetime.time(20, 00))
    zone = models.ForeignKey(WristbandAccessZone,verbose_name=_("Zone"),on_delete=models.CASCADE,blank=True,null=True,related_name="timetable")

    class Meta:
        verbose_name = _("Wristband Access Point")
        verbose_name_plural = _("Wristbands Access Points")

class WristbandAccessPoint(models.Model):
    in_point = models.BooleanField(verbose_name=_("In point"), default=False)
    close = models.BooleanField(verbose_name=_("Close"), default=False)
    uuid = models.CharField(max_length = 255, verbose_name= _('UUID'), default=new_ui_slug)
    name = models.CharField(max_length=255, verbose_name='Name', default="")
    zone = models.ForeignKey(WristbandAccessZone,verbose_name=_("Zone"),on_delete=models.CASCADE,blank=True,null=True,related_name="accesspoints")

    def is_open(self):
        now = datetime.datetime.now()
        for item in self.zone.timetable.all():
            i_time = now.replace(hour=item.ini_time.hour, minute=item.ini_time.minute)
            e_time = now.replace(hour=item.end_time.hour, minute=item.end_time.minute)
            if now > i_time and now < e_time:
                return True
        return False

    class Meta:
        verbose_name = _("Wristband Access Point")
        verbose_name_plural = _("Wristbands Access Points")

class WristbandAccessZoneGuest(models.Model):
    code = models.CharField(max_length=255, verbose_name=_('Code'), default="")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, verbose_name=_("Guest"), related_name="zones")
    zone = models.ForeignKey(WristbandAccessZone, verbose_name=_("Zone"), on_delete=models.CASCADE, blank=True, null=True, related_name="guests")

    class Meta:
        verbose_name = _("Wristband Access Zone Guest")
        verbose_name_plural = _("Wristbands Access Zone Guest")

class WristbandAccess(models.Model):
    inside = models.BooleanField(verbose_name=_("Inside"), default=False)
    date = models.DateTimeField(verbose_name=_('Date'), default=datetime.datetime.now)
    wristband = models.ForeignKey(Wristband, verbose_name=_("Wristband"), on_delete=models.CASCADE, blank=True, null=True, related_name="access")
    access_point = models.ForeignKey(WristbandAccessPoint,verbose_name=_("Access Point"),on_delete=models.SET_NULL,blank=True,null=True,related_name="accesspoints")

    @property
    def band_name(self):
        try:
            code = reverse_cardkey(self.wristband.code)
            return f"{self.wristband.name} ({code})"
        except:
            return ""

    @property
    def zone_name(self):
        try:
            return f"{self.access_point.zone.name}"
        except:
            return ""

    @property
    def guest_name(self):
        try:
            return f"{self.wristband.guest.name} {self.wristband.guest.surname}"
        except:
            return ""

    class Meta:
        verbose_name = _("Wristband access")
        verbose_name_plural = _("Wristbands access")
        ordering = ["-date"]

class WristbandBackup(models.Model):
    kid = models.BooleanField(verbose_name=_("Kid"), default=False)
    locks = models.BooleanField(verbose_name=_("Locks"), default=False)
    code = models.CharField(max_length=255, verbose_name=_('Code'), default="")
    name = models.CharField(max_length=255, verbose_name=_('Name'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")
    guest_uuid = models.CharField(max_length=255, verbose_name=_('Guest UUID'), default="")
    guest_name = models.CharField(max_length=255, verbose_name=_('Guest name'), default="")
    guest_mobile = models.CharField(max_length=255, verbose_name=_('Guest mobile'), default="")
    guest_email = models.CharField(max_length=255, verbose_name=_('Guest email'), default="")
    guest_room = models.CharField(max_length=255, verbose_name=_('Guest room'), default="")
    check_in = models.DateTimeField(verbose_name='Check-In', default=datetime.datetime.now)
    check_out = models.DateTimeField(verbose_name='Check-Out', default=datetime.datetime.now)
    type = models.CharField(max_length=255, verbose_name=_('Name'), default="")

    @property
    def balance(self):
        try:
            return self.balances.aggregate(Sum('amount'))["amount__sum"] if self.balances.count() > 0 else 0
        except Exception as e:
            print(e)
            return -1

    class Meta:
        verbose_name = _("Wristband backup")
        verbose_name_plural = _("Wristbands backups")

class WristbandBackupBalance(models.Model):
    date = models.DateTimeField(verbose_name=_('Date'), default=datetime.datetime.now)
    amount = models.FloatField(verbose_name=_('Amount'), default=0)
    desc = models.TextField(verbose_name=_("Description"), default="", blank=True)
    wristband = models.ForeignKey(WristbandBackup, verbose_name=_("Wristband"), on_delete=models.CASCADE, blank=True, null=True, related_name="balances")

    class Meta:
        verbose_name = _("Wristband backup balance")
        verbose_name_plural = _("Wristbands backup balance")




