from django.db import models

import datetime

class AnswerType(models.Model):
	field_type = models.CharField(max_length=20, verbose_name="Tipo de campo", default="")
	code = models.CharField(max_length=20, verbose_name="Codigo", default="")
	text = models.CharField(max_length=200, verbose_name="Nombre")

	def __str__(self):
		return self.text

	class Meta:
		verbose_name = 'Tipo de respuesta'
		verbose_name_plural = 'Tipos de respuesta'

class QuestionType(models.Model):
	code = models.CharField(max_length=10, verbose_name="Codigo", default="")
	text = models.CharField(max_length=200, verbose_name="Nombre")

	def __str__(self):
		return self.text

	class Meta:
		verbose_name = 'Tipo de pregunta'
		verbose_name_plural = 'Tipos de pregunta'

class Answer(models.Model):
	hide = models.BooleanField(verbose_name="Ocultar", default = False)
	text = models.CharField(max_length=200, verbose_name="Respuesta")
	#value = models.IntegerField(verbose_name="Valor", default=0)
	answer_type = models.ForeignKey(AnswerType, on_delete=models.CASCADE, verbose_name="Tipo de respuesta")

	def __str__(self):
		return self.text

	class Meta:
		verbose_name = 'Respuesta'
		verbose_name_plural = 'Respuestas'
		ordering = ['id']


class FormType(models.Model):
	code = models.CharField(max_length=10, verbose_name="Codigo", default="")
	name = models.CharField(max_length=200, verbose_name="Nombre")

	def __str__(self):
		return self.name

	class Meta:
		verbose_name = 'Tipo formulario'
		verbose_name_plural = 'Tipos de formulario'

class Block(models.Model):
    private = models.BooleanField(verbose_name="Privado", default=False)
    order = models.IntegerField(verbose_name="Orden", default=0)
    code = models.CharField(max_length=10, verbose_name="Codigo", default="")
    text = models.CharField(max_length=500, verbose_name="Texto")
    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE, verbose_name="Tipo Formulario", blank=True, null=True)

    def __str__(self):
        return "%s %s" % (self.code, self.text)

    def get_first_level_questions(self):
        return self.question_set.filter(parent__isnull=True)

    class Meta:
        verbose_name = '2.- Bloque de preguntas'
        verbose_name_plural = '2.- Bloques de preguntas'
        ordering = ['order']

class Question(models.Model):
    order = models.IntegerField(verbose_name="Orden", default=0)
    max_answers = models.IntegerField(verbose_name="Numero máximo de respuestas", default=1)
    code = models.CharField(max_length=10, verbose_name="Código", default="")
    text = models.CharField(max_length=500, verbose_name="Pregunta", default="", blank=True)
    question_type = models.ForeignKey(QuestionType, on_delete=models.CASCADE, verbose_name="Tipo de pregunta", blank=True, null=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, verbose_name="Bloque", blank=True, null=True)
    parent = models.ForeignKey('self', verbose_name="Padre", on_delete=models.CASCADE, blank=True, null=True, related_name="childs")

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = '3.- Pregunta'
        verbose_name_plural = '3.- Preguntas'
        ordering = ['order']

class Field(models.Model):
    obligatory = models.BooleanField(verbose_name="Obligatorio", default = False)
    read_only = models.BooleanField(verbose_name="Solo lectura", default = False)
    order = models.IntegerField(verbose_name="Orden", default=0)
    code = models.CharField(max_length=10, verbose_name="Codigo", default="")
    text = models.CharField(max_length=500, verbose_name="Pregunta")
    answer_type = models.ForeignKey(AnswerType, on_delete=models.CASCADE, verbose_name="Tipo de respuesta")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Pregunta", blank=True, null=True)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Campo'
        verbose_name_plural = 'Campos'
        ordering = ['order']

class Form(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")

    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE, verbose_name="Tipo Formulario", blank=True, null=True)
    blocks = models.ManyToManyField(Block, blank=True, verbose_name="Bloques de preguntas")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '2.- Formulario'
        verbose_name_plural = '2.- Formularios'

class FormInstance(models.Model):
    DRAFT = 's01'
    CONFIRMED = 's02'
    STATUS_CHOICES = [
        (DRAFT, 'Borrador'),
        (CONFIRMED, 'Confirmado'),
    ]

    code = models.CharField(verbose_name="Código", max_length=20, default="")

    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default=DRAFT)
    form = models.ForeignKey(Form, on_delete=models.CASCADE, verbose_name="Formulario", blank=True, null=True)

    def __str__(self):
        return "%s" % (self.code)

    def set_status(self, status_code):
        if status_code in {self.DRAFT, self.CONFIRMED}:
            self.status = status_code
            self.save()
            return True
        return False

    def is_confirmed(self):
        return (self.status != self.DRAFT)

    def check_obligatory(self, q, index):
        answers = self.answerinstance_set.filter(question=q, index=index, field__obligatory=True)
        for a in answers:
            if a.text != "" or a.document.name:
                return True
        return False
        
    def get_public_blocks(self):
        return self.form.blocks.filter(private=False)

    class Meta:
        verbose_name = '1.- Instancia de formulario'
        verbose_name_plural = '1.- Instancias de formulario'

def upload_document_file(instance, filename):
    ascii_filename = str(filename.encode('ascii', 'ignore'))
    instance.filename = ascii_filename
    folder = "cv/merits/%s" % (instance.form_instance.id) if instance.form_instance != None else "cv/merits"
    return '/'.join(['%s' % (folder), datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ascii_filename])

class AnswerInstance(models.Model):
    index = models.IntegerField(verbose_name="Indice", default=0)
    text = models.CharField(max_length=3000, verbose_name="Texto", default="")
    document = models.FileField(upload_to=upload_document_file, blank=True, verbose_name="Documento acreditativo", help_text="Select file to upload")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Pregunta", blank=True, null=True)
    field = models.ForeignKey(Field, on_delete=models.CASCADE, verbose_name="Campo", blank=True, null=True)
    form_instance = models.ForeignKey(FormInstance, on_delete=models.CASCADE, verbose_name="Formulario", blank=True, null=True)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Instancia de respuesta'
        verbose_name_plural = 'Instancias de respuesta'


