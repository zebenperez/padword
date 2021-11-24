# -*- encoding: utf-8 -*-

from django import template
from django.conf import settings

import os
import time
import datetime

register=template.Library()

'''
	Filter
'''
@register.filter
def keyvalue(dict, key):    
    return dict[key] if key in dict else {}

@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)

@register.filter
def divide(value, factor):
    try:
        return int(value/factor)
    except:
        return int(0)

'''
	Simple tag
'''
@register.simple_tag
def getkeyvalue(dict, key):    
    return dict[key].split("|")[0] if dict != None and key in dict else ""

@register.simple_tag
def getkeyvalue2(dict, prefix, key):    
	full_key = "{}{}".format(prefix, key)
	return "%0.2f" % float(dict[full_key]) if dict != None and full_key in dict else ""

@register.simple_tag
def getmaxrange(dict, key):    
	if key in dict:
		pos = len(dict[key]) - 1
		return dict[key][pos]
	return "0"

@register.simple_tag()
def get_file_name(name):
    name_list = name.split("/")
    return name_list[len(name_list)-1][15:] if len(name) > 15 else ""


