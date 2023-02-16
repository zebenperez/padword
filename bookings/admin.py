from django import forms
from django.contrib import admin, messages
from django.forms import ModelForm
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import *

'''
	Forms
'''
class InstanceForm(forms.Form):
	_selected_action = forms.CharField(widget=forms.MultipleHiddenInput)

'''
	Actions
'''
def duplicate_block(modeladmin, request, queryset):
	for b in queryset:
		block_order = b.order + 1
		#block = Block(order=block_order,code=b.code,text=b.text,form_type=b.form_type)
		block = Block(order=block_order,code=b.code,text=b.text)
		block.save()
		for q in b.question_set.all():
			question_order = q.order + 1
			question = Question(order=question_order,max_answers=q.max_answers,code=q.code,text=q.text,question_type=q.question_type,block=block)
			question.save()
			for f in q.field_set.all():
				field_order = f.order + 1
				field = Field(order=field_order,code=f.code,text=f.text,answer_type=f.answer_type,question=question)
				field.save()
duplicate_block.short_description = "Duplicar bloque"
	
'''
	Inlines
'''
class AnswerInline(admin.TabularInline):
	model = Answer
	extra = 1

class FieldInline(admin.TabularInline):
	model = Field
	extra = 1

class QuestionInline(admin.TabularInline):
	model = Question
	extra = 1

'''
	Admin
'''
class AnswerTypeAdmin(admin.ModelAdmin):
	list_display = ('code', 'text', 'field_type')
	inlines = [AnswerInline, ]

class BlockAdmin(admin.ModelAdmin):
	#list_display = ('code', 'form_type', 'text')
	list_display = ('code', 'text')
	#list_filter = ('form_type',)
	actions = [duplicate_block]

class FormAdmin(admin.ModelAdmin):
	list_display = ('name',)
	#filter_horizontal = ('blocks',)
	search_fields = ['channel']

class FormInstanceAdmin(admin.ModelAdmin):
    #list_display = ('pk', 'code', 'form', 'fill_form')
    list_display = ('pk', 'code', 'fill_form', 'form_type')
    search_fields = ['code']
    #list_filter = ('form__form_type',)
    list_per_page = 500

    def fill_form(self, obj):
        return mark_safe("<a href='%s' target='_blank'>Editar</a>" % (reverse('booking-view', args=[obj.id])))
    fill_form.short_description = 'Editar'

    def form_type(self, obj):
        if obj.form:
            return obj.form.form_type
        else:
            return None

    #def form(self, obj):
    #    return obj.form

class FormTypeAdmin(admin.ModelAdmin):
	list_display = ('code', 'name', 'template_base', 'template', 'template_login', 'order', 'main', 'project_uuid')

class QuestionAdmin(admin.ModelAdmin):
	list_display = ('block', 'code', 'text', 'order')
	inlines = [FieldInline, ]
	list_filter = ('block',)

class StatusAdmin(admin.ModelAdmin):
	list_display = ('code', 'name', 'color')

class GuestUserAdmin(admin.ModelAdmin):
	list_display = ('username', 'project_uuid', 'guest_uuid')

#admin.site.register(Answer)
admin.site.register(AnswerType, AnswerTypeAdmin)
admin.site.register(Block, BlockAdmin)
#admin.site.register(Field)
admin.site.register(Form, FormAdmin)
admin.site.register(FormInstance, FormInstanceAdmin)
admin.site.register(FormType, FormTypeAdmin)
admin.site.register(GuestUser, GuestUserAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(QuestionType)
admin.site.register(Status, StatusAdmin)

