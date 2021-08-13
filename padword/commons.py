from django.apps import apps
import sys
import datetime
import json
import string
import random


'''
    Exceptions
'''
def show_exc(e):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    return ("ERROR ===:> [%s in %s:%d]: %s" % (exc_type, exc_tb.tb_frame.f_code.co_filename, exc_tb.tb_lineno, str(e)))

'''
    Common
'''
def get_or_none(model, value, field="pk"):
    try:
        return model.objects.get(**{field: value})
    except Exception as e:
        return None

def get_or_none_str(app_name, model_name, value, field="pk"):
    try:
        model = apps.get_model(app_name, model_name)
        obj = model.objects.get(**{field: value})
        return obj
    except Exception as e:
        #logger.error("(get_object): %s" % e)
        return None

def set_obj_field(obj, field, value):
    obj_field = obj._meta.get_field(field)
    if obj_field.get_internal_type() == "ManyToManyField":
        getattr(obj, field).clear()
        for item in value:
            getattr(obj, field).add(get_or_none_str(obj._meta.app_label, obj_field.remote_field.model.__name__, item))
    elif obj_field.get_internal_type() == "ForeignKey":
        setattr(obj, field, get_or_none_str(obj._meta.app_label, obj_field.remote_field.model.__name__, value))
    elif obj_field.get_internal_type() == "FloatField":
        setattr(obj, field, value.replace(",", "."))
    elif obj_field.get_internal_type() == "BooleanField":
        setattr(obj, field, (value == "True"))
    elif obj_field.get_internal_type() == "DateTimeField":
        date = datetime.datetime.strptime(value, '%Y-%m-%d')
        if date >= datetime.datetime(1970,1,1):
            setattr(obj, field, date)
    else:
        setattr(obj, field, value)
    obj.save()

def get_param(dic, param, default=""):
    return dic[param] if param in dic and dic[param] != "" else default

def get_float(val):
    try:
        return float(val)
    except:
        return 0.0

def get_bool(val):
    try:
        return bool(val)
    except:
        return False

def translate(request, json_str):
    try:
        lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
        json_dict = json.loads(json_str)
        return json_dict[lang.upper()]
    except Exception as e:
        print (show_exc(e))
        return json.loads(json_str)['ES']

def new_ui_slug(model=None):
    slug = '{}-{}-{}-{}-{}'.format(''.join([random.choice(string.digits+'abcdef') for i in range(8)]),''.join([random.choice(string.digits+'abcdef') for i in range(4)]),''.join([random.choice(string.digits+'abcdef') for i in range(4)]),''.join([random.choice(string.digits+'abcdef') for i in range(4)]),''.join([random.choice(string.digits+'abcdef') for i in range(12)]))
    if model is None:
        while (model.objects.filter(uuid = slug).exists()):
            slug = '{}-{}-{}-{}-{}'.format(''.join([random.choice(string.digits+'abcdef') for i in range(8)]),''.join([random.choice(string.digits+'abcdef') for i in range(4)]),''.join([random.choice(string.digits+'abcdef') for i in range(4)]),''.join([random.choice(string.digits+'abcdef') for i in range(4)]),''.join([random.choice(string.digits+'abcdef') for i in range(12)]))
    return slug
