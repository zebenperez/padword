from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _ 

from datetime import datetime

from padword.commons import reverse_cardkey
from web.models_lock import Lock
from web.lock_lib import get_record_type as grt
from guest.models import KeyCode, KeyCard

register = template.Library()


'''
    Filter
'''
@register.filter
def get_code_type(value, date):
    end_date = datetime.fromtimestamp(date/1000.0)
    if value == 1:
        return _("One use")
    if value == 3 and end_date.year == 2099:
        return _("Permanent")
    return _("Period")

@register.filter
def get_card_type(date):
    end_date = datetime.fromtimestamp(date/1000.0)
    if end_date.year == 2099:
        return _("Permanent")
    return _("Period")

@register.filter
def get_code_guest(lock, code):
    key_code_list = KeyCode.objects.filter(lock=lock, code=code)
    result = ["{} {}".format(item.guest.name, item.guest.surname) for item in key_code_list]
    return mark_safe("<br/>".join(result))

@register.filter
def get_card_guest(lock, code):
    key_card_list = KeyCard.objects.filter(lock=lock, code=code)
    result = ["{} {}".format(item.guest.name, item.guest.surname) for item in key_card_list]
    return mark_safe("<br/>".join(result))

@register.filter
def get_ekey_link(lock, ekey_id):
    return ""

@register.filter
def get_reverse(code):
    return str(reverse_cardkey(code))

@register.filter
def get_room_locks(room):
    return Lock.objects.filter(project_uuid = room.project_uuid, room = room.number).order_by('pk') if room.number != "" else []

'''
    Simple Tags
'''
@register.simple_tag
def get_record_type(code):
    return grt(code)

'''
    Inclusion Tags
'''
@register.inclusion_tag('web/locks/gateway-level.html')
def get_gateway_icon(gateways, first=False):
    gateway_list = []
    try:
        g_list = gateways.split(";")
        for gateway in g_list:
            g = gateway.split("|")
            gateway_list.append({'name': g[0], 'level': int(g[1])})
            if first:
                break
    except: pass
    return {'gateway_list': gateway_list}
 
@register.inclusion_tag('web/locks/wifi-level.html')
def get_wifi_icon(wifis, first=False):
    wifi_list = []
    try:
        w_list = wifis.split(";")
        for wifi in w_list:
            w = wifi.split("|")
            wifi_list.append({'name': w[0], 'level': int(w[1]), 'online': int(w[2])})
            if first:
                break
    except: pass
    return {'wifi_list': wifi_list}
 
@register.inclusion_tag('web/gateways/lock-list.html')
def get_locks_by_gateway(project, gateway_id):
    lock_list = project.gateway_lock_list(gateway_id)
    lock = Lock.objects.filter(uuid=lock_list[0]["lockId"]).first() if len(lock_list) > 0 else None
    #gateway_name = lock.get_gateway_name_by_id(gateway_id) if lock != None else "Not found!"
    #return {'lock_list': lock_list, 'gateway_id': gateway_id, 'gateway_name': gateway_name}
    return {'lock_list': lock_list, 'gateway_id': gateway_id}

#@register.inclusion_tag('web/locks/record-type.html')
#def get_record_type(code):
#    return {'code': code}
 
