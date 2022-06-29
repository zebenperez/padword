#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [ 

    #--------------------- GUESTS --------------------
    path('', views.index, name='guest-index'),
    path('guests/', views.guests, name='guests'),
    path('guests/search/', views.guest_search, name='guest-search'),
    path('guests/form/', views.guest_form, name='guest-form'),
    path('guests/remove/', views.guest_remove, name='guest-remove'),
    path('guests/page/', views.guest_pagination, name='guest-page'),

    path('guests/project-<slug:project_id>/', views.guests_by_project, name='guests-by-project'),
    path('guests/project/form/', views.guest_form_by_project, name='guest-form-by-project'),

    #--------------------- GUESTS --------------------
    path('', views.index, name='device-index'),
    path('devices/', views.devices, name='guest-devices'),
    path('devices/search/', views.device_search, name='guest-device-search'),
    path('devices/form/', views.device_form, name='guest-device-form'),
    path('devices/room/', views.device_room, name='guest-device-room'),
    path('devices/remove/', views.device_remove, name='guest-device-remove'),
    path('devices/page/<int:page>/', views.device_pagination, name='guest-device-page'),

    #--------------------- NOTIFICATIONS --------------------
    path('guests/notifications/', views.notifications, name='guest-notifications'),
    path('guests/notifications/search/', views.notification_search, name='guest-notification-search'),
    path('guests/notifications/form/', views.notification_form, name='guest-notification-form'),
    path('guests/notifications/remove/', views.notification_remove, name='guest-notification-remove'),
    path('guests/notifications/send/', views.notification_send, name='guest-notification-send'),
    path('guests/notifications/page/', views.notification_pagination, name='guest-notification-page'),
    path('guests/notifications/autocomplete/', views.notification_autocomplete, name='guest-notification-autocomplete'),
    path('guests/notifications/add-guest/', views.notification_add_guest, name='guest-notification-add-guest'),
    path('guests/notifications/remove-guest/', views.notification_remove_guest, name='guest-notification-remove-guest'),

    #--------------------- CHAT --------------------
    path('guests/chat/show-chat/', views.show_chat, name="show-chat"),
    path('guests/chat/send-message/', views.message_send, name="send-message"),
    path('guests/chat/remove-message/', views.message_remove, name="remove-message"),
    path('guests/chat/check-messages/', views.messages_check, name="check-messages"),

    #--------------------- KEYS --------------------
    path('guests/keys/', views.keys, name="guest-keys"),
    path('guests/key/assign/', views.key_assign, name="guest-assign-key"),
    path('guests/key/remove/', views.key_remove, name="guest-remove-key"),
]

