from django.db import models
from django.utils.translation import ugettext as _
import datetime


class ProjectAvantioUser(models.Model):
    code_mobile = models.BooleanField(verbose_name=_('Get code from mobile'), default=False)
    days = models.IntegerField(verbose_name=_('Days to import'), default=1)
    days_new = models.IntegerField(verbose_name=_('Days to create'), default=1)
    hour = models.IntegerField(verbose_name=_('Hour to import'), default=0)
    minute = models.IntegerField(verbose_name=_('Minutes to import'), default=0)
    hour_notif = models.IntegerField(verbose_name=_('Hour to import notifications'), default=0)
    username = models.CharField(max_length=255, verbose_name=_('Username'), default="")
    password = models.CharField(max_length=255, verbose_name=_('Password'), default="")
    email = models.CharField(max_length=255, verbose_name=_('Email'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

class ProjectAvaibookUser(models.Model):
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    token = models.CharField(max_length=255, verbose_name=_('Token'), default="")
    owner = models.CharField(max_length=255, verbose_name=_('Owner'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

class ProjectWinhotelUser(models.Model):
    update_all_prices = models.BooleanField(verbose_name=_('Update all prices'), default=False)
    update_checkin = models.BooleanField(verbose_name=_('Update checkin'), default=False)
    days = models.IntegerField(verbose_name=_('Days to import'), default=1)
    hour = models.IntegerField(verbose_name=_('Hours to import'), default=-1)
    hour_price = models.IntegerField(verbose_name=_('Hours to import prices'), default=0)
    hour_cancel = models.IntegerField(verbose_name=_('Hours to cancel'), default=0)
    minute = models.IntegerField(verbose_name=_('Minutes to import notifications'), default=0)
    import_operator = models.IntegerField(verbose_name=_('Import operator'), default=1)
    source_code = models.CharField(max_length=255, verbose_name=_('Source code'), default="")
    target_code = models.CharField(max_length=255, verbose_name=_('Target code'), default="")
    ftp = models.CharField(max_length=900, verbose_name=_('FTP'), default="")
    ftp_filename = models.CharField(max_length=255, verbose_name=_('FTP Filename'), default="")
    ini_time = models.TimeField(_("Initial Time"), blank=True, default=datetime.time(14, 00))
    end_time = models.TimeField(_("End Time"), blank=True, default=datetime.time(12, 00))
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

class ProjectStripeUser(models.Model):
    api_key = models.CharField(max_length=255, verbose_name=_('Api Key'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

class ProjectMewsUser(models.Model):
    hour = models.IntegerField(verbose_name=_('Hour to import'), default=0)
    minute = models.IntegerField(verbose_name=_('Minutes to import'), default=0)
    client_token = models.CharField(max_length=255, verbose_name=_('Client Token'), default="")
    access_token = models.CharField(max_length=255, verbose_name=_('Access Token'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

class ProjectCloudbedsUser(models.Model):
    code_mobile = models.BooleanField(verbose_name=_('Get code from mobile'), default=False)
    hour = models.IntegerField(verbose_name=_('Hour to import'), default=0)
    minute = models.IntegerField(verbose_name=_('Minutes to import'), default=0)
    days = models.IntegerField(verbose_name=_('Days to import'), default=1)
    token = models.CharField(max_length=255, verbose_name=_('Token'), default="")
    ini_time = models.TimeField(_("Initial Time"), blank=True, default=datetime.time(14, 00))
    end_time = models.TimeField(_("End Time"), blank=True, default=datetime.time(12, 00))
    property_id = models.CharField(max_length=255, verbose_name=_('Property ID'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

class ProjectCarUser(models.Model):
    code = models.CharField(max_length=255, verbose_name=_('Code'), default="")
    description = models.CharField(max_length=255, verbose_name=_('Description'), default="")
    ftp = models.CharField(max_length=900, verbose_name=_('FTP'), default="")
    file_name = models.CharField(max_length=255, verbose_name=_('File Name'), default="")
    dir_name = models.CharField(max_length=255, verbose_name=_('Dir Name'), default="")
    minute = models.IntegerField(verbose_name=_('Minutes to import'), default=0)
    days = models.IntegerField(verbose_name=_('Days to import'), default=0)
    header_xml = models.TextField(verbose_name=_('Header XML'), default="")
    header_csv = models.TextField(verbose_name=_('Header CSV'), default="")

    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

class ProjectPaytefUser(models.Model):
    username = models.CharField(max_length=255, verbose_name=_('Username'), default="")
    password = models.CharField(max_length=255, verbose_name=_('Password'), default="")
    accessKey = models.CharField(max_length=255, verbose_name=_('accessKey'), default="")
    secretKey = models.CharField(max_length=255, verbose_name=_('secretKey'), default="")
    token = models.CharField(max_length=255, verbose_name=_('Token'), default="")
    tcod = models.CharField(max_length=255, verbose_name=_('TCOD'), default="")
    company = models.CharField(max_length=255, verbose_name=_('Company'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

class ProjectZktecoUser(models.Model):
    token = models.CharField(max_length=255, verbose_name=_('Token'), default="")
    dep = models.CharField(max_length=255, verbose_name=_('Department'), default="")
    server = models.CharField(max_length=255, verbose_name=_('Server'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

class ProjectRoomraccoonUser(models.Model):
    username = models.CharField(max_length=255, verbose_name=_('Username'), default="")
    password = models.CharField(max_length=255, verbose_name=_('Password'), default="")
    token = models.CharField(max_length=255, verbose_name=_('Token'), default="")
    pms = models.CharField(max_length=255, verbose_name=_('PMS'), default="")
    hotel = models.CharField(max_length=255, verbose_name=_('Hotel'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None

class ProjectOctorateUser(models.Model):
    client_id = models.CharField(max_length=255, verbose_name=_('Client ID'), default="")
    secret = models.CharField(max_length=255, verbose_name=_('Client Secret'), default="")
    token = models.CharField(max_length=255, verbose_name=_('Token'), default="")
    refresh = models.CharField(max_length=255, verbose_name=_('Refresh Token'), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_('Project UUID'), default="")

    @property
    def project(self):
        try:
            return Project.objects.get(uuid=self.project_uuid)
        except:
            return None


