from django.apps import apps
from django.db.models import Max
from django.contrib.auth.models import User
from .models import AnswerInstance, FormInstance, FormInstanceLog

import logging
logger = logging.getLogger(__name__)


'''
    Form functions
'''
def get_or_create_answer_instance(fi, q, f, index):
    ai, created = AnswerInstance.objects.get_or_create(form_instance=fi, question=q, field=f, index=index)
    return ai

def get_answer_instance(fi, q, f, index):
    return AnswerInstance.objects.filter(form_instance=fi, question=q, field=f, index=index).first()

def get_max_index(q, fi):
    max_index = AnswerInstance.objects.filter(form_instance = fi, question = q).aggregate(Max('index'))['index__max']
    return 0 if max_index == None else max_index

def get_form_instance(form_code, niu):
    return FormInstance.objects.filter(form__form_type__code = form_code, niu = niu).first()

def clone_form_instance(fi, vacancy):
    fi_id = fi.id
    new_fi = fi
    new_fi.pk = None
    new_fi.save()
    ai_list = AnswerInstance.objects.filter(form_instance__id = fi_id)
    for ai in ai_list:
        new_ai = ai
        new_ai.pk = None
        new_ai.form_instance = new_fi
        new_ai.save()

'''
    Common Functions
'''
def user_in_group(user, group_name):
    return bool(user.groups.filter(name=group_name))

def get_max_value(value, max_value):
    return get_float(value) if get_float(value) < get_float(max_value) else get_float(max_value)

def write_log(user, fi, text):
    FormInstanceLog.objects.create(user=user, form_instance=fi, text=text)

