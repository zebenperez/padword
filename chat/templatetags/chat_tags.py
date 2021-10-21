#!/usr/bin/python
#-*- coding: utf-8 -*- 
from django import template
from django.db.models import Q
from chat.models import *
import logging 
import random, string

from django.conf import settings 

logger = logging.getLogger(__name__) 
register = template.Library()

@register.simple_tag
def rand_str(str_len):
    return (''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(str_len)))


@register.simple_tag
def settings_value(name, default=""):
    return getattr(settings, name, default)



@register.filter
def is_subscriber(room, user):
    return room.is_subscriber(user)


@register.filter
def private_room_contact(room, user):
    try:
        return room.subscribers.exclude(pk=user.pk).first().username
    except Exception as e:
        logger.error(str(e))
    return room.name

@register.filter
def get_unreaded_messages(room, request):
    try:
        user = request.user
        current_room = request.session.get('room', Room.objects.filter(subscribers=user, active=True).order_by('code').first().code)
        if room.code != current_room:
            response = Message.objects.filter(room=room).exclude(Q(user=user)|Q(readed_by=user)).count()
            return response
    except Exception as e:
        logger.error(e)
    return 0
