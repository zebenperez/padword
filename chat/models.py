#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
from datetime import datetime as dt

from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
# from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
# from django.utils.translation import ugettext_lazy as _
from .utils import get_or_create
# Create your models here.

"""
 UTILS
"""
def messages_to_dic(messages_qs):
    # messages_list =  [{ 'user': m.user.username, 'user_pk': m.user.pk, 'date': m.creation_date.strftime("%d-%m-%Y %H:%M"), 'content': m.content , 'room':m.room.code, 'pk': m.pk} for m in messages_qs ]
    messages_list = [m.to_dict() for m in messages_qs]
    return sorted(messages_list, key=lambda d: d['pk'])

def file_name(instance, filename):
    extension = filename.split(".")[-1]
    fname = "_".join(filename.split(".")[:-1])
    return "/".join(["uploads", "%s.%s" % (slugify(fname), extension)])


class Room(models.Model):
    active = models.BooleanField(verbose_name=_("Activo"), default=True)
    code = models.SlugField(verbose_name=_("Codigo"), max_length=50, unique="True")
    creation_date = models.DateTimeField(verbose_name=_("Fecha de creación"), auto_now_add=True, null=True, blank=True)
    description = models.TextField(verbose_name="Descripción", blank=True, null=True)
    name = models.CharField(verbose_name=_("Nombre"), max_length=150, blank=True, null=True)
    owner = models.ForeignKey(User, verbose_name=_("Propietario"), on_delete=models.CASCADE)
    private = models.BooleanField(verbose_name=_("Conversacion Privada"), default=False)
    subscribers = models.ManyToManyField(User, verbose_name=_("Participantes"), related_name="user_rooms", blank=True)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Sala"
        verbose_name_plural = "Salas"

    def get_code(self):
        return slugify(self.name)

    def is_subscriber(self, user):
        return (self.subscribers.filter(pk=user.pk).exists())

    def last_message(self, user=None):
        last_message = self.room_messages.filter(deleted=False)
        if user:
            last_message = last_message.exclude(user=user)

        return last_message.order_by("-creation_date", "-pk").first()

    def last_message_dict(self, user=None):
        last_message = self.last_message(user)
        return {} if last_message is None else last_message.to_dict()

    def title(self, user=None):
        if self.private is True and user:
            return self.subscribers.exclude(pk=user.pk).first().username.capitalize()
        return self.name.capitalize()

    def to_dict(self, user=None):

        return {'pk': self.pk, 'private': self.private, 'code': self.code, 'name': self.title(user), 'url': reverse('chat_room', args=[self.code])}

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.get_code()
        super(Room, self).save(*args, **kwargs)


class Message(models.Model):
    creation_date = models.DateTimeField(verbose_name=_("Fecha de creación"), auto_now_add=True, null=True, blank=True)
    user = models.ForeignKey(User, verbose_name=_("Usuario"), on_delete=models.CASCADE, related_name="user_messages")
    room = models.ForeignKey(Room, verbose_name=_("Sala"), related_name="room_messages", on_delete=models.CASCADE)
    content = models.TextField(verbose_name=_("Contenido"), default="", blank=True, null=True)
    readed_by = models.ManyToManyField(User, verbose_name=_("Leido por"), related_name="readed_messages", blank=True)
    deleted = models.BooleanField(verbose_name=_("Borrado"), default=False)
    response_to = models.ForeignKey('Message', related_name="responses", blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return "[%s]%s-%s" % (self.creation_date, self.user, self.room)

    def to_dict(self):
        response_to = {}
        if self.response_to:
            response_to = {'user': self.response_to.user.username, 'content': self.response_to.content, 'pk': self.response_to.pk}

        return {
            'user': self.user.username, 'user_pk': self.user.pk, 'date': self.creation_date.strftime("%d-%m-%Y %H:%M"), 'content': self.content,
            'room': self.room.code, 'pk': self.pk, 'timestamp': self.timestamp, 'image': self.get_image_url, 'link': self.get_link_dict,
            'response_to': response_to
        }

    @property
    def timestamp(self):
        return time.mktime(self.creation_date.timetuple())

    class Meta:
        verbose_name = _("Mensaje")
        verbose_name_plural = _("Mensajes")

    @property
    def get_image_url(self):
        image = self.message_image.all().first()
        if image:
            return image.image.url
        else:
            return False

    @property
    def get_link_dict(self):
        link = self.message_link.all().first()
        if link:
            return {'link': link.link, 'text': link.link_text}
        else:
            return False


class MessageLink(models.Model):
    message = models.ForeignKey(Message, verbose_name="Mensaje", related_name="message_link", on_delete=models.CASCADE)
    link = models.URLField(max_length=300, verbose_name="Enlace")
    link_text = models.CharField(max_length=300, verbose_name="Texto del enlace", blank=True, null=True)

    def __str__(self):
        return "[%s] %s" % (self.link, self.link_text)

    class Meta:
        verbose_name = _("Enlace")
        verbose_name_plural = _("Enlaces")


class MessageImage(models.Model):
    message = models.ForeignKey(Message, verbose_name="Mensaje", related_name="message_image", on_delete=models.CASCADE)
    image = models.ImageField(upload_to=file_name, verbose_name="Imagen")

    class Meta:
        verbose_name = _("Imagen")
        verbose_name_plural = _("Imagenes")


class LastConnection(models.Model):
    date = models.DateTimeField(verbose_name=_("Fecha"), default=dt.min, null=True, blank=True)
    user = models.ForeignKey(User, verbose_name=_("Usuario"), on_delete=models.CASCADE)
    room = models.ForeignKey(Room, verbose_name=_("Sala"), related_name="rooms_lastcons", on_delete=models.CASCADE)

    def __str__(self):
        return "%s -> %s" % (self.user.username, self.room.name)

    def set_to_now(self):
        self.date = dt.now()
        self.save()

    @property
    def timestamp(self):
        return time.mktime(self.date.timetuple())

    class Meta:
        verbose_name = "Last Connections"
        verbose_name_plural = "Last Connections"
        unique_together = ['user', 'room']
