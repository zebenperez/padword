from django.apps import apps
from django.conf import settings
from dateutil import tz
import sys
import datetime
import time
import json
import string
import random
import unicodedata
import os
import subprocess
import pytz

import logging
logger = logging.getLogger(__name__)

'''
    Exceptions
'''
def show_exc(e):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    return ("ERROR ===:> [%s in %s:%d]: %s" % (exc_type, exc_tb.tb_frame.f_code.co_filename, exc_tb.tb_lineno, str(e)))

'''
    Users
'''
def user_in_group(user, group):
    return user.groups.filter(name=group).exists()

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
        if "-" in value:
            date = datetime.datetime.strptime(value, '%Y-%m-%d')
            if date >= datetime.datetime(1970,1,1):
                setattr(obj, field, date)
        if ":" in value:
            val = datetime.datetime.strptime("{} {}".format(getattr(obj, field).strftime('%Y-%m-%d'), value), '%Y-%m-%d %H:%M')
            setattr(obj, field, val)
    else:
        setattr(obj, field, value)
    obj.save()

def get_param(dic, param, default=""):
    return dic[param] if param in dic and dic[param] != "" else default

def get_float(val):
    try:
        return float(val.replace(",", "."))
    except:
        return 0.0

def get_bool(val):
    try:
        return bool(val)
    except:
        return False

def get_int(val):
    try:
        return int(val)
    except Exception as e:
        return 0

def translate(request, json_str):
    try:
        lang = request.GET['lang'] if 'lang' in request.GET else request.LANGUAGE_CODE
        json_dict = json.loads(json_str)
        return json_dict[lang.upper()]
    except Exception as e:
        try:
            return json.loads(json_str)['ES']
        except Exception as e:
            return (json_str)

def translate2(lang, json_str):
    try:
        json_dict = json.loads(json_str)
        return json_dict[lang.upper()]
    except Exception as e:
        try:
            return json.loads(json_str)['ES']
        except Exception as e:
            return (json_str)


def new_ui_slug(model=None, field="uuid"):
    slug = '{}-{}-{}-{}-{}'.format(''.join([random.choice(string.digits+'abcdef') for i in range(8)]),''.join([random.choice(string.digits+'abcdef') for i in range(4)]),''.join([random.choice(string.digits+'abcdef') for i in range(4)]),''.join([random.choice(string.digits+'abcdef') for i in range(4)]),''.join([random.choice(string.digits+'abcdef') for i in range(12)]))
    if model is not None:
        kwarg = {field: slug}
        #while (model.objects.filter(uuid = slug).exists()):
        while (model.objects.filter(**kwarg).exists()):
            slug = '{}-{}-{}-{}-{}'.format(''.join([random.choice(string.digits+'abcdef') for i in range(8)]),''.join([random.choice(string.digits+'abcdef') for i in range(4)]),''.join([random.choice(string.digits+'abcdef') for i in range(4)]),''.join([random.choice(string.digits+'abcdef') for i in range(4)]),''.join([random.choice(string.digits+'abcdef') for i in range(12)]))
            kwarg = {field: slug}
    return slug

def normalize_str(string):
    try:
        return unicodedata.normalize('NFKD', unicode(string,"utf-8")).encode('ascii', 'ignore')
    except:
        return unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')

def get_items_per_page():
    try:
        return settings.ITEMS_PER_PAGE
    except:
        return 20

def reverse_cardkey(cardReader_value):
    try:
        n = 2
        hex_value   = str(hex(int(cardReader_value)))
        hex_value = hex_value[2:]
        hex_value = f'{hex_value:>8s}'
        hex_value = hex_value.replace(' ','0')
        reverse_hex = [hex_value[idx:idx + n] for idx in range(0, len(hex_value), n)]
        reverse_hex = ''.join(reversed(reverse_hex))
        return (int(reverse_hex, 16))
    except:
        return (0)

def set_session(request, key, default=""):
    request.session[key] = request.GET[key] if key in request.GET else default

def get_random_str(n):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))

def get_random_digits(n):
    return ''.join(random.choice(string.digits) for _ in range(n))

def timestamp_to_date(value):
    return datetime.datetime.fromtimestamp(value/1000.0).strftime("%Y-%m-%d %H:%M:%S")

def date_to_utc(date, timezone):
    #local = pytz.timezone("Atlantic/Canary")
    local = pytz.timezone(timezone)
    try:
        local_dt = local.localize(date, is_dst=None)
    except:
        new_date = datetime.datetime(date.year, date.month, date.day, date.hour, date.minute, date.second)
        local_dt = local.localize(new_date, is_dst=None)
    date_utc = local_dt.astimezone(pytz.utc)
    return date_utc

def date_to_local(date, timezone):
    return date.astimezone(tz.gettz(timezone))

'''
    External scripts
'''
def update_cron(hour, minute, function, project_uuid):
    #logger.error("[common-update-cron] --1--")
    #path = os.path.join(settings.BASE_DIR, "padword", "update_cron.sh")
    path = os.path.join(settings.BASE_DIR, "update_cron.sh")
    #print("{} {} {} {} {}".format(path, hour, minute, function, project_uuid))
    print("{} {} {} {} {} {} {}".format(path, hour, minute, function, project_uuid, settings.BASE_DIR, settings.SYSPATH))
    print(subprocess.run(["{} {} {} {} {} {} {}".format(path, hour, minute, function, project_uuid, settings.BASE_DIR, settings.SYSPATH)], shell=True))


