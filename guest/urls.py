#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views, wristband_views, stripe_views

urlpatterns = [ 

    #--------------------- GUESTS --------------------
    path('', views.index, name='guest-index'),
    path('guests/', views.guests, name='guests'),
    path('guests/search/', views.guest_search, name='guest-search'),
    path('guests/page/', views.guest_page, name='guest-page'),
    path('guests/form/', views.guest_form, name='guest-form'),
    #path('guests/form-simple/', views.guest_form_simple, name='guest-form-simple'),
    #path('guests/remove/<int:obj_id>/', views.guest_remove, name='guest-remove'),
    path('guests/remove/', views.guest_remove, name='guest-remove'),
    path('guests/soft-remove/<int:obj_id>/', views.guest_soft_remove, name='guest-soft-remove'),
    #path('guests/page/', views.guest_pagination, name='guest-page'),
    path('guests/details/<int:obj_id>/', views.guest_details, name='guest-details'),
    path('guests/details/', views.guest_details, name='guest-details'),
    path('guests/stripe-update/', views.guest_stripe_update, name='guest-stripe-update'),

    path('guests/project/', views.guests_by_project, name='guests-by-project'),
    path('guests/project/search', views.guest_search_by_project, name='guest-search-by-project'),
    path('guests/project/page', views.guest_page_by_project, name='guest-page-by-project'),
    path('guests/project/form/', views.guest_form_by_project, name='guest-form-by-project'),
    path('guests/project/remove/', views.guest_remove_by_project, name='guest-remove-by-project'),
    path('guests/project/soft-remove/<int:obj_id>/', views.guest_soft_remove_by_project, name='guest-soft-remove-by-project'),
    path('guests/project/soft-remove-all/', views.guest_soft_remove_all_by_project, name='guest-soft-remove-all-by-project'),
    path('guests/project/details/<int:obj_id>/', views.guest_details_by_project, name='guest-details-by-project'),
    path('guests/project/details/', views.guest_details_by_project, name='guest-details-by-project'),

    path('guests/update-code/', views.guest_update_code, name='guest-update-code'),
    path('guests/save-date/', views.guest_save_date, name='guest-save-date'),
    path('guests/save-room/', views.guest_save_room, name='guest-save-room'),

    path('guests/rooms/autocomplete/', views.guest_room_autocomplete, name='guest-room-autocomplete'),

    path('guests/set-regime/', views.guest_set_regime, name='guest-set-regime'),

    #--------------------- WRISTBANDS --------------------
    path('guests/band/details', wristband_views.guest_band_details, name='guest-band-details'),
    path('guests/band/add', wristband_views.guest_band_add, name='guest-band-add'),
    path('guests/band/edit', wristband_views.guest_band_edit, name='guest-band-edit'),
    path('guests/band/save', wristband_views.guest_band_save, name='guest-band-save'),
    path('guests/band/name', wristband_views.guest_band_name, name='guest-band-name'),
    path('guests/band/type', wristband_views.guest_band_type, name='guest-band-type'),
    path('guests/band/balance/add/', wristband_views.guest_band_balance_add, name="guest-band-balance-add"),
    path('guests/band/kid/', wristband_views.guest_band_kid, name="guest-band-kid"),
    path('guests/band/locks/', wristband_views.guest_band_locks, name="guest-band-locks"),
    path('guests/band/remove', wristband_views.guest_band_remove, name='guest-band-remove'),
    path('guests/band/remove2', wristband_views.guest_band_remove2, name='guest-band-remove2'),
    path('guests/band/balance/', wristband_views.guest_bands_balance, name="guest-bands-balance"),
    path('guests/band/balance/list/', wristband_views.guest_band_balance_list, name="guest-band-balance-list"),
    path('guests/band/balance/form/', wristband_views.guest_band_balance_form, name="guest-band-balance-form"),
    path('guests/band/balance/remove/', wristband_views.guest_band_balance_remove, name="guest-band-balance-remove"),
    path('guests/band/manage-zone/', wristband_views.guest_band_manage_zone, name="guest-band-manage-zone"),

    path('wristbands/', wristband_views.wristbands, name='wristbands'),
    path('wristbands/search/', wristband_views.wristbands_search, name='wristbands-search'),
    path('wristbands/project/', wristband_views.wristbands_by_project, name='wristbands-by-project'),
    path('wristbands/project/search/', wristband_views.wristbands_search_by_project, name='wristbands-search-by-project'),

    path('wristbands-access/', wristband_views.wristbands_access, name='wristbands-access'),
    path('wristbands-access/search/', wristband_views.wristbands_access_search, name='wristbands-access-search'),
    path('wristbands-access/index/<slug:project_uuid>/<slug:point_uuid>/', wristband_views.wristbands_access_index, name='wristbands-access-index'),
    path('wristbands-access/send/', wristband_views.wristbands_access_send, name='wristbands-access-send'),

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

    path('guests/key-card-all/', views.key_card_all, name="guest-key-card-all"),
    path('guests/key-add-card-all/', views.key_add_card_all, name="guest-key-add-card-all"),

    path('ext/find-card/<slug:project_uuid>/<slug:ext_id>/', views.key_card_all_ext, name="guest-key-card-all-ext"),
    path('ext/add-card/', views.key_add_card_all_ext, name="guest-key-add-card-all-ext"),
    #path('guests/keys/', views.keys, name="guest-keys"),
    #path('guests/key/assign/', views.key_assign, name="guest-assign-key"),
    #path('guests/key/remove/', views.key_remove, name="guest-remove-key"),

    #--------------------- STRIPE --------------------
    path('stripe/alta-client/<str:uuid_guest>', stripe_views.stripe_alta_client, name='stripe-alta-client'),
    path('stripe/store-payment/<str:session_id>', stripe_views.stripe_store_payment, name='stripe-store-payment'),
    path('stripe/error-payment/<str:session_id>', stripe_views.stripe_error_payment, name='stripe-error-payment'),
    #path('stripe/do-payment/', stripe_views.stripe_payment, name='stripe-payment'),

    #-------------------- WRISTBANDS PAY --------------#
    path('wristbands/pay-access/<slug:project_uuid>/', wristband_views.pay_access, name='wristband-pay-access'),
    path('wristbands/pay-login/', wristband_views.pay_login, name='wristband-pay-login'),
    path('wristbands/pay-login-form/', wristband_views.pay_login_form, name='wristband-pay-login-form'),
    path('wristbands/pay-close/', wristband_views.pay_close, name='wristband-pay-close'),
    path('wristbands/pay-confirm/', wristband_views.pay_confirm, name='wristband-pay-confirm'),
    #path('wristbands/pay-confirm/<slug:payment_intent>/<slug:payment_intent_client_secret>/<slug:source_type>', wristband_views.pay_confirm, name='wristband-pay-confirm'),
    path('wristbands/pay-send/', wristband_views.pay_send, name='wristband-pay-send'),
    path('wristbands/pay-index/<slug:project_uuid>/', wristband_views.pay_index, name='wristband-pay-index'),
 
]

