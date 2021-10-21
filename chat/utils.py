# -*
# - coding: utf-8 -*-
import unicodedata
import string
import random
from datetime import datetime
from itertools import chain
from operator import attrgetter
from django.core.exceptions import ObjectDoesNotExist

import logging
logger = logging.getLogger(__name__)

def normalize_str(string):
    try:
        return unicodedata.normalize('NFKD', unicode(string, "utf-8")).encode('ascii', 'ignore')
    except Exception:
        return unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')


def random_string(size=12):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for i in range(size))

def random_string_prefix(prefix, size=12):
    code = prefix + random_string(size)[:-len(prefix)]
    return code

def now_str():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def get_or_none(model, pk):
    try:
        return model.objects.get(pk=pk)
    except Exception:
        print("get_or_none_exception for model %s" % model)
        return None

def get_or_none_query(model, query):
    try:
        return model.objects.get(**query)
    except Exception:
        return None

def get_or_create(model, query):
    try:
        return model.objects.get(**query)
    except ObjectDoesNotExist:
        return model.objects.create(**query)
    except Exception as e:
        logger.error(str(e))
        return None

def get_or_create_query(model, get_query, create_query):
    try:
        return model.objects.get(**get_query)
    except ObjectDoesNotExist:
        return model.objects.create(**create_query)
    except Exception as e:
        logger.error(str(e))
        return None


def update_or_none(model, query, update):
    try:
        return model.objects.filter(**query).update(**update)
    except Exception as e:
        logger.warning(str(e))
        return None

def join_and_short_qs(*args, **kwargs):

    if 'order_by' in kwargs:
        order_field = kwargs.pop('order_by')
        results = sorted(chain(*args), key=attrgetter(order_field))
        return results

    else:
        return list(chain(*args))

def pop_element(dic, key):
    value = None
    if key in dic:
        value = dic.get(key, None)
        del dic[key]

    return value

def get_model_fields(model):
    return [f.name for f in model._meta.get_fields()]


def list_get(lst, index, default=None):
    try:
        if index >= 0:
            return lst[index]
        else:
            index = len(lst) + index  # los querysets no soportan indexado negativo
            return lst[index]
    except Exception:
        return default
