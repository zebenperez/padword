from django.db import models
from django.db.models import Max
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _ 

from contents.models import Category, Item, ShoppingCart
from web.models import Channel, Device, Project
from guest.models import Guest

from padword.commons import show_exc

import datetime


def get_int(val):
    try:
        return int(val)
    except:
        return 0

class Status(models.Model):
	code = models.CharField(max_length=20, verbose_name=_("Code"), default="")
	name = models.CharField(max_length=200, verbose_name=_("Name"))

	def __str__(self):
		return self.name

	class Meta:
		verbose_name = _('Status')
		verbose_name_plural = _('Status')

class AnswerType(models.Model):
	field_type = models.CharField(max_length=20, verbose_name=_("Field type"), default="")
	code = models.CharField(max_length=20, verbose_name=_("Code"), default="")
	text = models.CharField(max_length=200, verbose_name=_("Name"))

	def __str__(self):
		return self.text

	class Meta:
		verbose_name = _('Answer type')
		verbose_name_plural = _('Answers types')

class QuestionType(models.Model):
	code = models.CharField(max_length=10, verbose_name=_("Code"), default="")
	text = models.CharField(max_length=200, verbose_name=_("Name"))

	def __str__(self):
		return self.text

	class Meta:
		verbose_name = _('Question type')
		verbose_name_plural = _('Questions types')

class Answer(models.Model):
	hide = models.BooleanField(verbose_name=_("Hide"), default = False)
	text = models.CharField(max_length=200, verbose_name=_("Answer"))
	#value = models.IntegerField(verbose_name="Valor", default=0)
	answer_type = models.ForeignKey(AnswerType, on_delete=models.CASCADE, verbose_name=_("Answer type"))

	def __str__(self):
		return self.text

	class Meta:
		verbose_name = _('Answer')
		verbose_name_plural = _('Answers')
		ordering = ['id']

class FormType(models.Model):
    order = models.BooleanField(default=False, verbose_name="Order")
    code = models.CharField(max_length=10, verbose_name=_("Code"), default="")
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    template = models.CharField(max_length=200, verbose_name=_("Template"), default="", blank=True)
    project_uuid = models.CharField(max_length=255, verbose_name=_("Project UUID"), default="")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Form type')
        verbose_name_plural = _('Forms type')
        ordering = ['name']

def upload_form_image(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "forms/images/%s" % (instance.id)
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

def upload_form_logo(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "forms/logs/%s" % (instance.id)
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

def upload_form_qr(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "forms/qr/%s" % (instance.id)
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

class Form(models.Model):
    active = models.BooleanField(default=False, help_text=_("This form is active for guests"), verbose_name="Active")
    show_desc = models.BooleanField(default=False, help_text=_("Show description"), verbose_name="Show description")
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="")
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    category = models.CharField(max_length=200, verbose_name=_("Category"), default="")
    image = models.ImageField(upload_to=upload_form_image, blank=True, verbose_name="Imagen de fondo", help_text="Select file to upload")
    logo = models.ImageField(upload_to=upload_form_logo, blank=True, verbose_name="Logo", help_text="Select file to upload")
    qr = models.ImageField(upload_to=upload_form_qr, blank=True, verbose_name="QR", help_text="Select file to upload")
    desc = models.TextField(verbose_name=_("Description"), default="", blank=True)
    desc_width = models.CharField(max_length=10, verbose_name=_("Description Width"), default="100", blank=True)

    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE, verbose_name=_("Form type"), blank=True, null=True)
    #blocks = models.ManyToManyField(Block, blank=True, verbose_name=_("Questions blocks"))

    def __str__(self):
        return self.name

    def get_category_items(self):
        cat = Category.objects.filter(uuid = self.category).first()
        return cat.get_items if cat != None else []

    @property
    def get_category(self):
        cat = Category.objects.filter(uuid = self.category).first()
        return cat

    @property
    def project(self):
        cat = Category.objects.filter(uuid = self.category).first()
        return cat.project if cat != None else None

    def get_public_blocks(self):
        return self.blocks.filter(private=False)

    class Meta:
        verbose_name = _('2.- Form')
        verbose_name_plural = _('2.- Forms')
        ordering = ['name']

class Block(models.Model):
    private = models.BooleanField(verbose_name=_("Private"), default=False)
    order = models.IntegerField(verbose_name=_("Order"), default=0)
    code = models.CharField(max_length=10, verbose_name=_("Code"), default="")
    text = models.CharField(max_length=500, verbose_name=_("Text"))
    form = models.ForeignKey(Form, on_delete=models.CASCADE, verbose_name=_("Form"), blank=True, null=True, related_name="blocks")
    #form_type = models.ForeignKey(FormType, on_delete=models.CASCADE, verbose_name=_("Form type"), blank=True, null=True)

    def __str__(self):
        return "%s %s" % (self.code, self.text)

    def get_first_level_questions(self):
        return self.question_set.filter(parent__isnull=True)

    @staticmethod
    def get_max_order(form):
        return get_int(Block.objects.filter(form=form).aggregate(Max('order'))["order__max"]) + 1

    class Meta:
        verbose_name = _('3.- Question block')
        verbose_name_plural = _('3.- Questions blocks')
        ordering = ['order']

class Question(models.Model):
    order = models.IntegerField(verbose_name=_("Order"), default=0)
    max_answers = models.IntegerField(verbose_name=_("Max number of answers"), default=1)
    code = models.CharField(max_length=10, verbose_name=_("Code"), default="")
    text = models.CharField(max_length=500, verbose_name=_("Question"), default="", blank=True)
    question_type = models.ForeignKey(QuestionType, on_delete=models.CASCADE, verbose_name=_("Question type"), blank=True, null=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, verbose_name=_("Block"), blank=True, null=True)
    parent = models.ForeignKey('self', verbose_name=_("Parent"), on_delete=models.CASCADE, blank=True, null=True, related_name="childs")

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = _('4.- Question')
        verbose_name_plural = _('4.- Questions')
        ordering = ['order']

class Field(models.Model):
    obligatory = models.BooleanField(verbose_name=_("Obligatory"), default = False)
    read_only = models.BooleanField(verbose_name=_("Read only"), default = False)
    order = models.IntegerField(verbose_name=_("Order"), default=0)
    code = models.CharField(max_length=10, verbose_name=_("Code"), default="")
    text = models.CharField(max_length=500, verbose_name=_("Question"))
    answer_type = models.ForeignKey(AnswerType, on_delete=models.CASCADE, verbose_name=_("Answer type"), blank=True, null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name=_("Question"), blank=True, null=True)

    def __str__(self):
        return self.text
    
    @staticmethod
    def get_max_order(q):
        return get_int(Field.objects.filter(question=q).aggregate(Max('order'))["order__max"]) + 1

    class Meta:
        verbose_name = _('Field')
        verbose_name_plural = _('Fields')
        ordering = ['order']

class FormChannel(models.Model):
    channel = models.CharField(max_length=200, verbose_name=_("Channel"), default="")
    form = models.ForeignKey(Form, on_delete=models.CASCADE, verbose_name=_("Form"), blank=True, null=True, related_name="channels")

    @property
    def channel_name(self):
        channel = Channel.objects.filter(uuid=self.channel).first()
        return channel.name if channel != None else ""

class FormInstance(models.Model):
    code = models.CharField(verbose_name=_("Code"), max_length=20, default="")
    date = models.DateTimeField(_('Creation date'), default=datetime.datetime.now, null=True)
    guest_uuid = models.CharField(max_length=255, verbose_name=_("Guest UUID"), default="")
    form_uuid = models.CharField(max_length=255, verbose_name=_("Form UUID"), default="")
    #status = models.ForeignKey(Status, on_delete=models.SET_NULL, verbose_name=_("Status"), blank=True, null=True)

    def __str__(self):
        return "%s" % (self.code)

    @property
    def guest(self):
        return Guest.objects.filter(UUID = self.guest_uuid).first()

    @property
    def form(self):
        return Form.objects.filter(uuid = self.form_uuid).first()

    @property
    def device(self):
        if self.form != None and self.form.project != None and self.guest != None:
            return Device.objects.filter(channel__project__uuid = self.form.project.uuid, room = self.guest.room).first()
        return None

    @property
    def get_total(self):
        try:
            items = ShoppingCart.objects.filter(form_instance_id=self.pk)
            total_price = 0
            for item in items:
                total_price += float(item.item.price.replace(',','.'))
            return total_price
        except Exception as e:
            print (show_exc(e))
            return 0

    @property
    def get_status(self):
        return self.status_list.all().first()

    def check_obligatory(self, q, index):
        answers = self.answerinstance_set.filter(question=q, index=index, field__obligatory=True)
        for a in answers:
            if a.text != "" or a.document.name:
                return True
        return False
        
    def get_public_blocks(self):
        return self.form.blocks.filter(private=False)

    def set_status(self, status_code, user="", comment=""):
        status = Status.objects.filter(code = status_code).first()
        if status != None:
            FormInstanceStatus.objects.create(form_instance=self, status=status, user=user, comment=comment)
            #self.status = status
            #self.save()

    def items_in_bookings(self, item):
        items = ShoppingCart.objects.filter(form_instance_id=self.pk, item=item)
        return (items)

    @property
    def get_items(self):
        items = ShoppingCart.objects.filter(form_instance_id=self.pk)
        return (items)

 
    class Meta:
        verbose_name = _('1.- Form instance')
        verbose_name_plural = _('1.- Form instances')
        ordering = ['-date']

def upload_document_file(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "cv/merits/%s" % (instance.form_instance.id) if instance.form_instance != None else "cv/merits"
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

class AnswerInstance(models.Model):
    index = models.IntegerField(verbose_name=_("Index"), default=0)
    text = models.CharField(max_length=3000, verbose_name=_("Text"), default="")
    document = models.FileField(upload_to=upload_document_file, blank=True, verbose_name=_("Document"), help_text="Select file to upload")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name=_("Question"), blank=True, null=True)
    field = models.ForeignKey(Field, on_delete=models.CASCADE, verbose_name=_("Field"), blank=True, null=True)
    form_instance = models.ForeignKey(FormInstance, on_delete=models.CASCADE, verbose_name=_("Form"), blank=True, null=True)

    def __str__(self):
        return self.text

    def get_item(self):
        return Item.objects.filter(uuid = self.text).first()

    class Meta:
        verbose_name = _('Answer instance')
        verbose_name_plural = _('Answer instances')

class FormInstanceStatus(models.Model):
    date = models.DateTimeField('date', auto_now_add=True)
    user = models.CharField(max_length=100, verbose_name=_("User"), default="")
    comment = models.CharField(max_length=100, verbose_name=_("Text"), default="")
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, verbose_name=_("Status"), blank=True, null=True)
    form_instance = models.ForeignKey(FormInstance, on_delete=models.CASCADE, verbose_name=_("Form instance"), blank=True, null=True, related_name="status_list")

    def __str__(self):
        return self.status

    class Meta:
        verbose_name = _('Form Instance Status')
        verbose_name_plural = _('Form Instance Status')
        ordering = ['-date']

class FormInstanceLog(models.Model):
	date = models.DateTimeField('date', auto_now_add=True)
	user = models.CharField(max_length=100, verbose_name=_("User"), default="")
	text = models.CharField(max_length=100, verbose_name=_("Text"), default="")
	form_instance = models.ForeignKey(FormInstance, on_delete=models.CASCADE, verbose_name=_("Form instance"), blank=True, null=True, related_name="logs")

	def __str__(self):
		return self.text

	class Meta:
		verbose_name = _('Form log')
		verbose_name_plural = _('Form logs')

class GuestUser(models.Model):
    guest_uuid = models.CharField(max_length = 255, verbose_name= _('Guest UUID'), default='admin')
    project_uuid = models.CharField(max_length = 255, verbose_name= _('Project UUID'), default='admin')
    username = models.CharField(max_length = 255, verbose_name= _('Username'), default='admin')

    class Meta:
        verbose_name = _('Guest user')

    @property
    def guest(self):
        try:
            return Guest.objects.get(UUID=self.guest_uuid)
        except:
            return None

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
    def get_or_create_guest_user(guest_uuid, project_uuid, username):
        try:
            user = User.objects.get(username=username)
        except:
            try:
                guests_group = Group.objects.get(name='guests') 
                user = User.objects.create_user(username, email=username) if "@" in username else User.objects.create_user(username)
                guests_group.user_set.add(user)
            except Exception as e:
                return None, str(e)
        gu, created = GuestUser.objects.get_or_create(guest_uuid=guest_uuid, project_uuid=project_uuid, username=user.username)
        return user, ""


