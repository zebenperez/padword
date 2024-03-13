from django.db import models
from django.db.models import Count, Max
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _ 

from contents.models import Category, Item, ShoppingCart, PaymentType, PointOfSale, Table
from web.models import Channel, Device, Project
from guest.models import Guest, Wristband

from .email_lib import send_change_status_email
from padword.commons import show_exc, translate2

import datetime
import threading


def get_int(val):
    try:
        return int(val)
    except:
        return 0

class Status(models.Model):
    code = models.CharField(max_length=20, verbose_name=_("Code"), default="")
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    color = models.CharField(max_length=10, verbose_name=_("Color"), default="")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Status')
        verbose_name_plural = _('Status')

#class Table(models.Model):
#    uuid = models.CharField(max_length = 255, verbose_name= _('UUID'), default="")
#    name = models.CharField(max_length=200, verbose_name=_("Name"))
#    pos_uuid = models.CharField(max_length=255, verbose_name=_("POS UUID"), default="", blank=True)

#    def __str__(self):
#        return self.name

#    class Meta:
#        verbose_name = _('Table')
#        verbose_name_plural = _('Tables')
#        ordering = ['name']

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

def upload_form_type_css(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "form_types/css/"
    return '/'.join(['%s' % (folder), ascii_filename])

class FormType(models.Model):
    main = models.BooleanField(default=False, verbose_name="Main")
    order = models.BooleanField(default=False, verbose_name="Order")
    code = models.CharField(max_length=10, verbose_name=_("Code"), default="")
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    template = models.CharField(max_length=200, verbose_name=_("Template"), default="", blank=True)
    template_base = models.CharField(max_length=200, verbose_name=_("Template Base"), default="", blank=True)
    template_login = models.CharField(max_length=200, verbose_name=_("Template Login"), default="", blank=True)
    project_uuid = models.CharField(max_length=255, verbose_name=_("Project UUID"), default="", blank=True)
    css = models.FileField(upload_to=upload_form_type_css, blank=True, verbose_name=_("CSS"), help_text="Select file to upload")

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
    uuid = models.CharField(max_length=255, verbose_name=_('UUID'), default="", unique=True)
    name = models.CharField(max_length=200, verbose_name=_("Name"))
    category = models.CharField(max_length=200, verbose_name=_("Category"), default="")
    image = models.ImageField(upload_to=upload_form_image, blank=True, verbose_name="Imagen de fondo", help_text="Select file to upload")
    logo = models.ImageField(upload_to=upload_form_logo, blank=True, verbose_name="Logo", help_text="Select file to upload")
    qr = models.ImageField(upload_to=upload_form_qr, blank=True, verbose_name="QR", help_text="Select file to upload")
    desc = models.TextField(verbose_name=_("Description"), default="", blank=True)
    desc_width = models.CharField(max_length=10, verbose_name=_("Description Width"), default="100", blank=True)
    desc_out_of_order = models.TextField(verbose_name=_("Description out of order"), default="", blank=True)

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

    @property
    def get_email_texts(self):
        email_texts = self.email_texts.first()
        if email_texts == None:
            email_texts = FormEmailText(form=self)
            email_texts.email_from = '{"ES": "info@padword.es"}' 
            email_texts.subject_new = '{"ES": "Nuevo pedido __SERVICE_NAME__"}' 
            email_texts.subject_change = '{"ES": "Cambio de estado del pedido __SERVICE_NAME__"}'
            email_texts.body_new = '{"ES": "Se ha creado el pedido __SERVICE_NAME__ del usuario __USER__ (habitación __ROOM__) <br/><br/> <a href=\'__URL__\'>Pinche aquí para ver las reservas </a>"}'
            email_texts.body_change = '{"ES": "El pedido __SERVICE_NAME__ del usuario __USER__ (habitación __ROOM__) ha cambiado al estado __STATUS__ <br/><br/> <a href=\'__URL__\'>Pinche aquí para ver las reservas </a>"}'
            email_texts.save()
        return email_texts

    def get_public_blocks(self):
        return self.blocks.filter(private=False)

    def get_category_uuid_by_code(self, code):
        cat = Category.objects.filter(project_uuid=self.project.uuid, internal=code).first()
        return cat.uuid if cat != None else ""

    def get_common_items(self):
        fi_list = [fi.id for fi in FormInstance.objects.filter(form_uuid=self.uuid)]
        item_list = list(ShoppingCart.objects.filter(form_instance_id__in=fi_list).values_list('item', flat=True).annotate(total=Count('item')).order_by('-total')[:2])
        return Item.objects.filter(id__in=item_list)

    def to_tickets(self, start_id="", start_date="", end_date="", status=""):
        if start_date != "" and end_date != "":
            s_date = datetime.datetime.strptime(start_date, "%Y-%m-%d_%H:%M")
            e_date = datetime.datetime.strptime(end_date, "%Y-%m-%d_%H:%M")
            fi_list = FormInstance.objects.filter(form_uuid=self.uuid, date__range=(s_date, e_date))
        elif start_id != "":
            fi_list = FormInstance.objects.filter(pk__gte=start_id, form_uuid=self.uuid).order_by("id")
        else:
            fi_list = FormInstance.objects.filter(form_uuid=self.uuid)
        resp = {"tickets": []}
        for fi in fi_list:
            st = translate2("es", fi.get_status.status.name) if fi.get_status != None else ""
            if status == "" or status.lower() == st.lower():
                pos_name = fi.pos.name if fi.pos != None else ""
                table_name = fi.table.name if fi.table != None else ""
                guest_name = fi.guest.name if fi.guest != None else ""
                lang = fi.details.lang if fi.details != None else ""
                payment_type = translate2("es", fi.payment_type.name) if fi.payment_type != None else ""
                #total = fi.get_total * -1 if fi.payment_type != None and "04" in fi.payment_type.code else fi.get_total
                fi_json = {
                    'id': fi.id, 
                    'fecha': fi.date.strftime("%d-%m-%Y"), 
                    'hora': fi.date.strftime("%H:%M:%S"), 
                    'total': fi.amount, 
                    'punto de venta': pos_name, 
                    'mesa': table_name,
                    'cliente': guest_name,
                    'idioma': lang,
                    'estado': st,
                    'tipo de pago': payment_type,
                    'elementos': []
                }
                for item in fi.get_items:
                    #category_name = item.item.category.name if item.item.category != None else ""
                    low_price = item.low_price if item.low_price > -1 else item.price
                    item_json = {
                        'nombre_servicio': item.name,
                        'id_servicio': item.id,
                        'cantidad': 1,
                        'precio_servicio': item.price,
                        'precio_servicio_reducido': low_price,
                        'subtotal': 0,
                        'familia': item.category,
                        'id_articulo_pms': 0
                    }
                    fi_json["elementos"].append(item_json)
                resp["tickets"].append(fi_json)
        return resp

    @staticmethod
    def get_main(project):
        ft = FormType.objects.filter(project_uuid = project.uuid, main = True).first()
        return Form.objects.filter(form_type = ft).first()

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

class FormEmail(models.Model):
    email = models.CharField(max_length=400, verbose_name=_("Email"), default="")
    form = models.ForeignKey(Form, on_delete=models.CASCADE, verbose_name=_("Form"), blank=True, null=True, related_name="emails")

class FormEmailText(models.Model):
    email_from = models.CharField(max_length=200, verbose_name=_("Email From"), default="")
    subject_new = models.CharField(max_length=900, verbose_name=_("Subject New"), default="")
    subject_change = models.CharField(max_length=900, verbose_name=_("Subject Change"), default="")
    body_new = models.TextField(verbose_name=_("Body New"), default="", blank=True)
    body_change = models.TextField(verbose_name=_("Body Change"), default="", blank=True)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, verbose_name=_("Form"), blank=True, null=True, related_name="email_texts")

class FormTimetable(models.Model):
    monday = models.BooleanField(verbose_name=_("Monday"), default=False)
    tuesday = models.BooleanField(verbose_name=_("Tuesday"), default=False)
    wednesday = models.BooleanField(verbose_name=_("Wednesday"), default=False)
    thursday = models.BooleanField(verbose_name=_("Thursday"), default=False)
    friday = models.BooleanField(verbose_name=_("Friday"), default=False)
    saturday = models.BooleanField(verbose_name=_("Saturday"), default=False)
    sunday = models.BooleanField(verbose_name=_("Sunday"), default=False)
    ini_time = models.TimeField(_("Initial Time"), blank=True, default=datetime.time(00, 00))
    end_time = models.TimeField(_("End Time"), blank=True, default=datetime.time(00, 00))
    form = models.ForeignKey(Form, on_delete=models.CASCADE, verbose_name=_("Form"), blank=True, null=True, related_name="timetables")

    def check_day(self, day):
        if day == 0 and self.monday:
            return True
        elif day == 1 and self.tuesday:
            return True
        elif day == 2 and self.wednesday:
            return True
        elif day == 3 and self.thursday:
            return True
        elif day == 4 and self.friday:
            return True
        elif day == 5 and self.saturday:
            return True
        elif day == 6 and self.sunday:
            return True
        return False

    def check_time(self, time):
        ini_time = (self.ini_time.hour * 60) + self.ini_time.minute
        end_time = (self.end_time.hour * 60) + self.end_time.minute
        return (ini_time <= time and end_time >= time)

class FormInstance(models.Model):
    code = models.CharField(verbose_name=_("Code"), max_length=20, default="")
    date = models.DateTimeField(_('Creation date'), default=datetime.datetime.now, null=True)
    guest_uuid = models.CharField(max_length=255, verbose_name=_("Guest UUID"), default="")
    guest_name = models.CharField(max_length=255, verbose_name=_("Guest name"), default="")
    form_uuid = models.CharField(max_length=255, verbose_name=_("Form UUID"), default="")
    pos_uuid = models.CharField(max_length=255, verbose_name=_("Point of sale UUID"), default="")
    table_uuid = models.CharField(max_length=255, verbose_name=_("Table UUID"), default="")
    #status = models.ForeignKey(Status, on_delete=models.SET_NULL, verbose_name=_("Status"), blank=True, null=True)
    amount = models.CharField(max_length=100, verbose_name=_("Amount to pay"), default="")
    payment_type = models.ForeignKey(PaymentType, on_delete=models.SET_NULL, verbose_name=_("Payment Type"), blank=True, null=True)

    def __str__(self):
        return "%s" % (self.code)

    @property
    def guest(self):
        return Guest.objects.filter(UUID = self.guest_uuid).first()

    @property
    def form(self):
        return Form.objects.filter(uuid = self.form_uuid).first()

    @property
    def pos(self):
        return PointOfSale.objects.filter(uuid = self.pos_uuid).first()

    @property
    def table(self):
        return Table.objects.filter(uuid = self.table_uuid).first()

    @property
    def details(self):
        return self.info.first()

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
                try:
                    #total_price += float(item.item.price.replace(',','.'))
                    total_price += float(item.price.replace(',','.'))
                except:
                    total_price += 0
            return total_price
        except Exception as e:
            print (show_exc(e))
            return 0

    @property
    def get_total_low(self):
        try:
            items = ShoppingCart.objects.filter(form_instance_id=self.pk)
            total_price = 0
            for item in items:
                try:
                    total_price += float(item.low_price(',','.'))
                except:
                    total_price += 0
            return total_price
        except Exception as e:
            print (show_exc(e))
            return 0

    @property
    def band(self):
        info = self.info.first()
        if info == None:
            return None
        return Wristband.get_active_by_project(self.form.project, info.band)

    @property
    def get_status(self):
        return self.status_list.all().first()

    @property
    def get_items(self):
        items = ShoppingCart.objects.filter(form_instance_id=self.pk)
        return (items)

    def get_total_by_regime(self, regime):
        try:
            items = ShoppingCart.objects.filter(form_instance_id=self.pk)
            total_price = 0
            for item in items:
                try:
                    price = item.item.get_price(regime, self.band)
                    total_price += float(price)
                except Exception as ex:
                    #print(ex)
                    total_price += 0
            if self.band != None and self.band.guest != None and self.band.guest.guest_type_obj != None:
                total_price = total_price - (total_price * (self.band.guest.guest_type_obj.discount / 100))
            return total_price
        except Exception as e:
            print (show_exc(e))
            return 0

    def get_invalid_item(self, regime):
        items = ShoppingCart.objects.filter(form_instance_id=self.pk)
        for item in items:
            price = item.item.get_price(regime, self.band)
            if price == None:
                return True
        return False

    def check_obligatory(self, q, index):
        answers = self.answerinstance_set.filter(question=q, index=index, field__obligatory=True)
        for a in answers:
            if a.text != "" or a.document.name:
                return True
        return False
        
    def get_public_blocks(self):
        #print(self.form.uuid)
        #print(self.form.blocks.all())
        return self.form.blocks.filter(private=False)

    def set_status(self, status_code, user="", comment=""):
        status = Status.objects.filter(code = status_code).first()
        if status != None:
            FormInstanceStatus.objects.create(form_instance=self, status=status, user=user, comment=comment)
            t = threading.Thread(target=send_change_status_email, args=[self, status], daemon=True)
            t.start()
            #send_change_status_email(self, status)
            #self.status = status
            #self.save()

    def items_in_bookings(self, item):
        items = ShoppingCart.objects.filter(form_instance_id=self.pk, item=item)
        return (items)

    def update_item_low_price(self, item):
        band = self.band
        if band != None and band.guest != None:
            gr = band.guest.regimes.first()
            if gr != None and gr.regime != None:
                item.low_price = item.item.get_price(gr.regime.code)
                item.save()

    def update_items_low_price(self):
        for item in self.get_items:
            self.update_item_low_price(item)

#    def update_items_low_price(self):
#        band = self.band
#        if band != None and band.guest != None:
#            gr = band.guest.regimes.first()
#            if gr != None and gr.regime != None:
#                for item in self.get_items:
#                    item.low_price = item.item.get_price(gr.regime.code)
#                    item.save()

    @staticmethod
    def get_all_items(guest):
        if guest == None:
            return []
        fi_list = FormInstance.objects.filter(guest_uuid = guest.UUID, status_list__isnull = True).values_list('pk', flat=True)
        return ShoppingCart.objects.filter(form_instance_id__in = list(fi_list)).order_by('form_instance_id')
 
    @staticmethod
    def get_open_in_table(pos, table):
        form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=pos.project_uuid).first()
        return FormInstance.objects.filter(form_uuid=form.uuid, pos_uuid = pos.uuid, table_uuid = table.uuid, status_list__isnull = True)
        #return FormInstance.objects.filter(pos_uuid = pos.uuid, table_uuid = table.uuid, status_list__isnull = True).first()

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
        uuid = self.text if "|" not in self.text else self.text.split("|")[0]
        return Item.objects.filter(uuid = uuid).first()

    class Meta:
        verbose_name = _('Answer instance')
        verbose_name_plural = _('Answer instances')

class FormInstanceStatus(models.Model):
    read = models.BooleanField(verbose_name=_("Read"), default=False)
    date = models.DateTimeField('date', auto_now_add=True)
    user = models.CharField(max_length=100, verbose_name=_("User"), default="")
    comment = models.CharField(max_length=100, verbose_name=_("Text"), default="")
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, verbose_name=_("Status"), blank=True, null=True)
    form_instance = models.ForeignKey(FormInstance, on_delete=models.CASCADE, verbose_name=_("Form instance"), blank=True, null=True, related_name="status_list")

    def __str__(self):
        return self.status.name if self.status != None else ""

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
        uname = "guest_{}".format(username)
        try:
            user = User.objects.get(username=uname)
        except:
            try:
                guests_group = Group.objects.get(name='guests') 
                #user = User.objects.create_user(username, email=username) if "@" in username else User.objects.create_user(username)
                user = User.objects.create_user(uname)
                guests_group.user_set.add(user)
            except Exception as e:
                return None, str(e)
        gu, created = GuestUser.objects.get_or_create(guest_uuid=guest_uuid, project_uuid=project_uuid, username=user.username)
        return user, ""

    @staticmethod
    def delete_by_guest(guest_uuid):
        gu_list = GuestUser.objects.filter(guest_uuid=guest_uuid).delete()

class FormInstanceInfo(models.Model):
    pos = models.CharField(max_length=255, verbose_name=_("Point of service"), default="")
    table = models.CharField(max_length=255, verbose_name=_("Table"), default="")
    band = models.CharField(max_length=255, verbose_name=_("Band"), default="")
    client = models.CharField(max_length=255, verbose_name=_("Guest name"), default="")
    client_id = models.CharField(max_length=255, verbose_name=_("Guest name"), default="")
    client_mobile = models.CharField(max_length=255, verbose_name=_("Guest mobile"), default="")
    client_email = models.CharField(max_length=255, verbose_name=_("Guest email"), default="")
    client_room = models.CharField(max_length=255, verbose_name=_("Guest room"), default="")
    desc = models.CharField(max_length=900, verbose_name=_("Description"), default="")
    fi = models.ForeignKey(FormInstance, on_delete=models.CASCADE, verbose_name=_("Form Instance"), null=True, blank=True, related_name='info')

    @property
    def lang(self):
        try:
            guest = Guest.objects.filter(id=int(self.client_id)).first()
            return guest.language if guest != None else ""
        except:
            return ""

class Cash(models.Model):
    close = models.BooleanField(_('Close'), default=False)
    date = models.DateTimeField(_('Creation date'), default=datetime.datetime.now, null=True)
    ini_cash = models.FloatField(verbose_name='Initial amount', default=-1, null=True, blank=True)
    end_cash = models.FloatField(verbose_name='Final amount', default=0, null=True, blank=True)
    band = models.FloatField(verbose_name='Band amount', default=0, null=True, blank=True)
    card = models.FloatField(verbose_name='Card amount', default=0, null=True, blank=True)
    free = models.FloatField(verbose_name='Free amount', default=0, null=True, blank=True)
    back = models.FloatField(verbose_name='Back amount', default=0, null=True, blank=True)
    back_card = models.FloatField(verbose_name='Back amount', default=0, null=True, blank=True)
    back_band = models.FloatField(verbose_name='Back amount', default=0, null=True, blank=True)
    val1 = models.FloatField(verbose_name='Summary amount 1', default=0, null=True, blank=True)
    val2 = models.FloatField(verbose_name='Summary amount 2', default=0, null=True, blank=True)
    username = models.CharField(max_length = 255, verbose_name= _('Username'), default='admin')
    pos_uuid = models.CharField(max_length=255, verbose_name=_("Point of sale UUID"), default="")
    project_uuid = models.CharField(max_length=255, verbose_name=_("Project UUID"), default="", blank=True)

    @property
    def pos(self):
        return PointOfSale.objects.filter(uuid = self.pos_uuid).first()

    @property
    def project(self):
        return Project.objects.filter(uuid = self.project_uuid).first()

