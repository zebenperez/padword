# !/usr/bin/python
# -*- coding: utf-8 -*-

from django.urls import path

import chat.views as views
import chat.generic as gviews


urlpatterns = [
    path('', views.index, name="chat_index"),
    path('room/form/', views.chat_room_form, name="chat_room_form"),
    # path('rooms/list/', views.rooms_list, name="rooms_list"),
    path('room/messages/<str:code>/', views.chat_room, name="chat_room"),
    path('room/messages/page/<str:code>/', views.get_messages_page , name="get_page"),
    path('room/subscriber/form/<str:code>/', views.room_subscribers_form, name="room_subscribers_form"),
    path('room/message/image/form/<str:code>/', views.message_image_form, name="message_image_form"),
    path('room/deactivate/<str:code>/', views.deactivate_room, name="deactivate_room"),


    # generic
    path('form_save/<str:app>/<str:form_class_name>/', gviews.form_save, name="form_save"),
    # test
    # path('stream/', pviews.stream, name="sse"),
    # path('stream/view', pviews.stream_view, name="stream_view")

    # feed
    path('feed/message/receiver/', views.message_receiver, name="message_receiver"),
    path('feed/reading/confirmation/<str:code>/', views.reading_confirmation, name="reading_confirmation"),


    # dispatcher
    path('dispatcher/notification/', views.notification_dispatcher, name="notification_dispatcher"),
]

