from django.apps import apps
from django.db.models import Max
from django.contrib.auth.models import User
from PIL import Image
from .models import AnswerInstance, FormInstance, FormInstanceLog

import qrcode, io
import logging
logger = logging.getLogger(__name__)


'''
    Form functions
'''
def get_or_create_form_instance(form_uuid, guest_uuid):
    fi, created = FormInstance.objects.get_or_create(form_uuid=form_uuid, guest_uuid=guest_uuid, status__isnull=True)
    return fi

def get_or_create_answer_instance(fi, q, f, index):
    ai, created = AnswerInstance.objects.get_or_create(form_instance=fi, question=q, field=f, index=index)
    return ai

def get_answer_instance(fi, q, f, index):
    return AnswerInstance.objects.filter(form_instance=fi, question=q, field=f, index=index).first()

def get_max_index(q, fi):
    max_index = AnswerInstance.objects.filter(form_instance = fi, question = q).aggregate(Max('index'))['index__max']
    return 0 if max_index == None else max_index

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

def generate_qr(data, logo, color, color_back):
    qr = qrcode.QRCode( version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    if logo != None and logo != "":
        img = qr.make_image(fill_color=color, back_color=color_back).convert('RGB')

        basewidth = 100
        img_logo = Image.open(logo)
        wpercent = (basewidth / float(img_logo.size[0]))
        hsize = int((float(img_logo.size[1]) * float(wpercent)))
        img_logo = img_logo.resize((basewidth, hsize), Image.ANTIALIAS)

        pos = ((img.size[0] - img_logo.size[0]) // 2, (img.size[1] - img_logo.size[1]) // 2)
        img.paste(img_logo, pos)
    else:
        img = qr.make_image(fill_color=color, back_color=color_back)

    byteIO = io.BytesIO()
    img.save(byteIO, format='PNG')
    byteArr = byteIO.getvalue()

    return byteArr

'''
    Common Functions
'''
def user_in_group(user, group_name):
    return bool(user.groups.filter(name=group_name))

def get_max_value(value, max_value):
    return get_float(value) if get_float(value) < get_float(max_value) else get_float(max_value)

def write_log(user, fi, text):
    FormInstanceLog.objects.create(user=user, form_instance=fi, text=text)

