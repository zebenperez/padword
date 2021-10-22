#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.forms import ModelForm, CharField
from django.utils.html import escape
from .models import Room, Message, MessageImage, MessageLink
import re


class RoomSimpleForm(ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'description', 'owner', 'subscribers']


class MessageRoomForm(ModelForm):
    message_identifier = CharField(label="Message identifier")

    def clean_content(self):
        content = escape(self.cleaned_data['content'])
        content = content.replace("\n", "<br/>")
        urls = re.findall(r'(https?://\S+)', content)
        for url in set(urls):
            link = "<a href='%s' target='_blank'>%s</a>" % (url, url)
            content = content.replace(url, link)
            
        return content

    class Meta:
        model = Message
        fields = ['user', 'room', 'content', 'message_identifier', "readed_by", "response_to"]


class MessageImageForm(ModelForm):
    class Meta:
        model = MessageImage
        fields = "__all__"


class RoomSubscribersForm(ModelForm):
    class Meta:
        model = Room
        fields = ['subscribers']


class MessageLinkForm(ModelForm):
    class Meta:
        model = MessageLink
        exclude = []
