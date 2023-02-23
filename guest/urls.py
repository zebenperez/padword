#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [ 

    #--------------------- GUESTS --------------------
    path('', views.index, name='guest-index'),
    path('guests/', views.guests, name='guests'),
    path('guests/search/', views.guest_search, name='guest-search'),
    path('guests/page/', views.guest_page, name='guest-page'),
    path('guests/form/', views.guest_form, name='guest-form'),
    #path('guests/form-simple/', views.guest_form_simple, name='guest-form-simple'),
    path('guests/remove/', views.guest_remove, name='guest-remove'),
    path('guests/soft-remove/', views.guest_soft_remove, name='guest-soft-remove'),
    #path('guests/page/', views.guest_pagination, name='guest-page'),

    path('guests/project/', views.guests_by_project, name='guests-by-project'),
    path('guests/project/search', views.guest_search_by_project, name='guest-search-by-project'),
    path('guests/project/page', views.guest_page_by_project, name='guest-page-by-project'),
    path('guests/project/form/', views.guest_form_by_project, name='guest-form-by-project'),
    path('guests/project/remove/', views.guest_remove_by_project, name='guest-remove-by-project'),
    path('guests/project/soft-remove/', views.guest_soft_remove_by_project, name='guest-soft-remove-by-project'),

    path('guests/update-code/', views.guest_update_code, name='guest-update-code'),
    path('guests/save-date/', views.guest_save_date, name='guest-save-date'),
    path('guests/save-room/', views.guest_save_room, name='guest-save-room'),

    path('guests/rooms/autocomplete/', views.guest_room_autocomplete, name='guest-room-autocomplete'),

    path('guests/set-regime/', views.guest_set_regime, name='guest-set-regime'),

    #--------------------- DEVICES --------------------
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
    path('guests/key-open/', views.key_open, name="guest-key-open"),
    path('guests/key-change-code/', views.key_change_code, name="guest-key-change-code"),
    #path('guests/key-remove-code/', views.key_remove_code, name="guest-key-remove-code"),

    path('guests/key-add-card/', views.key_add_card, name="guest-key-add-card"),
    path('guests/key-remove-card/', views.key_remove_card, name="guest-key-remove-card"),
    #path('guests/keys/', views.keys, name="guest-keys"),
    #path('guests/key/assign/', views.key_assign, name="guest-assign-key"),
    #path('guests/key/remove/', views.key_remove, name="guest-remove-key"),
]

