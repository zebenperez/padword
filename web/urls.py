#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views, auto_views, room_views, card_views, lock_views, lock_user_views, lock_group_views, gateway_views

urlpatterns = [ 
    #path('index/<slug:chk>/', views.index, name='web-index-new'),
    path('index/', views.index, name='web-index-new'),
    path('', views.index, name='web-index'),
    #--------------------- Projects --------------------
    path('projects/company-<int:company_id>/', views.projects, name='projects-by-company'),
    path('projects/project-<slug:project_id>/', views.projects, name='projects-by-uuid'),
    path('projects/', views.projects, name='projects'),
    path('projects/search/', views.project_search, name='project-search'),
    path('projects/form/', views.project_form, name='project-form'),
    path('projects/remove/', views.project_remove, name='project-remove'),
    path('projects/upload-json/', views.project_upload_json, name='project-upload-json'),
    path('projects/user-token/', views.project_user_token, name='project-user-token'),
    #--------------------- Channels --------------------
    path('channels/project-<slug:project_id>/', views.channels, name='channels-by-project'),
    path('channels/company-<slug:company_id>/', views.channels, name='channels-by-company'),
    path('channels/', views.channels, name='channels'),
    path('channels/search/', views.channel_search, name='channel-search'),
    path('channels/form/', views.channel_form, name='channel-form'),
    path('channels/remove/', views.channel_remove, name='web-channel-remove'),
    #--------------------- Companies --------------------
    path('companies/', views.companies, name='companies'),
    path('companies/search/', views.company_search, name='company-search'),
    path('companies/form/', views.company_form, name='company-form'),
    path('companies/remove/', views.company_remove, name='company-remove'),
    #--------------------- Devices --------------------
    path('devices/project-<int:project_id>/', views.devices_by_project, name='devices-by-project'),
    path('devices/channel-<int:channel_id>/', views.devices_by_channel, name='devices-by-channel'),
    path('devices/company-<int:company_id>/', views.devices_by_project, name='devices-by-company'),
    path('devices/', views.devices, name='devices'),
    path('devices/search/', views.device_search, name='device-search'),
    path('devices/form/', views.device_form, name='device-form'),
    path('devices/assign/', views.device_assign, name='device-assign'),
    path('devices/remove/', views.device_remove, name='device-remove'),
    #--------------------- Locks --------------------
    #path('locks/', lock_views.locks, name='locks'),
    path('locks-by-project/<int:project_id>/', lock_views.locks_by_project, name='locks-by-project'),
    path('locks/search/', lock_views.lock_search, name='lock-search'),
    path('locks/form/', lock_views.lock_form, name='lock-form'),
    path('locks/remove/', lock_views.lock_remove, name='lock-remove'),
    path('locks/get-all-passcodes/', lock_views.lock_get_all_passcodes, name='lock-get-all-passcodes'),
    path('locks/remove/code/', lock_views.lock_remove_code, name='lock-remove-code'),
    path('locks/get-all-cards/', lock_views.lock_get_all_cards, name='lock-get-all-cards'),
    path('locks/remove/card/', lock_views.lock_remove_card, name='lock-remove-card'),
    path('locks/set-action/', lock_views.lock_set_action, name='lock-set-action'),
    path('locks/share-code/', lock_views.lock_share_code, name='lock-share-code'),
    path('locks/share-code-guest/', lock_views.lock_share_code_guest, name='lock-share-code-guest'),
    #--------------------- LocksUsers --------------------
    path('locks-users/', lock_user_views.locks_users, name='locks-users'),
    path('locks-users/search/', lock_user_views.lock_user_search, name='lock-user-search'),
    path('locks-users/form/', lock_user_views.lock_user_form, name='lock-user-form'),
    path('locks-users/set-password/', lock_user_views.lock_user_set_password, name='lock-user-set-password'),
    path('locks-users/register/', lock_user_views.lock_user_register, name='lock-user-register'),
    path('locks-users/remove/', lock_user_views.lock_user_remove, name='lock-user-remove'),
    path('locks-users/remove-by-username/', lock_user_views.lock_user_remove_by_username, name='lock-user-remove-by-username'),
    #--------------------- LocksGroups --------------------
    #path('locks-groups/', lock_group_views.locks_groups, name='locks-groups'),
    path('locks-groups-by-project/<int:project_id>/', lock_group_views.locks_groups_by_project, name='locks-groups-by-project'),
    path('locks-groups/search/', lock_group_views.lock_group_search, name='lock-group-search'),
    path('locks-groups/form/', lock_group_views.lock_group_form, name='lock-group-form'),
    path('locks-groups/save/', lock_group_views.lock_group_save, name='lock-group-save'),
    path('locks-groups/remove/', lock_group_views.lock_group_remove, name='lock-group-remove'),
    path('locks-groups/remove-by-id/', lock_group_views.lock_group_remove_by_id, name='lock-group-remove-by-id'),
    path('locks-groups/add/', lock_group_views.lock_group_add, name='lock-group-add'),
    #--------------------- Rooms --------------------
    path('rooms/', room_views.rooms, name='rooms'),
    #path('rooms/search/', room_views.room_search, name='room-search'),
    #path('rooms/floors/', room_views.room_floors, name='room-floors'),
    path('rooms/list/', room_views.room_list, name='room-list'),
    path('rooms/form/', room_views.room_form, name='room-form'),
    path('rooms/remove/', room_views.room_remove, name='room-remove'),
    path('rooms/search/', room_views.rooms_search, name='rooms-search'),
    path('rooms/lock-details/', room_views.room_lock_details, name='room-lock-details'),
    path('rooms/lock-list/', room_views.room_lock_list, name='room-lock-list'),
    path('rooms/set-group/', room_views.room_set_group, name='room-set-group'),
    #path('rooms/lock-add/', room_views.room_lock_add, name='room-lock-add'),
    path('rooms/lock-add-card/', room_views.room_lock_add_card, name='room-lock-add-card'),
    path('rooms/lock-remove-card/', room_views.room_lock_remove_card, name='room-lock-remove-card'),
    path('rooms/lock-add-code/', room_views.room_lock_add_code, name='room-lock-add-code'),
    path('rooms/lock-remove-code/', room_views.room_lock_remove_code, name='room-lock-remove-code'),
    path('rooms/lock-add-ekey/', room_views.room_lock_add_ekey, name='room-lock-add-ekey'),
    path('rooms/lock-remove-ekey/', room_views.room_lock_remove_ekey, name='room-lock-remove-ekey'),
    path('ekey-url/<slug:token>//', room_views.ekey_url, name='ekey-url'),
    #--------------------- Rooms by projects --------------------
    path('rooms/by-project/', room_views.rooms_by_project, name='rooms-by-project'),
    path('rooms/list/by-project/', room_views.room_list_by_project, name='room-list-by-project'),
    path('rooms/form/by-project/', room_views.room_form_by_project, name='room-form-by-project'),

    #--------------------- KeyCard --------------------
    path('keycards/', card_views.keycards, name='keycards'),
    path('keycards/search/', card_views.keycard_search, name='keycard-search'),
    path('keycards/form/', card_views.keycard_form, name='keycard-form'),
    path('keycards/remove/', card_views.keycard_remove, name='keycard-remove'),

    #--------------------- Gateways --------------------
    path('gateways-by-project/<int:project_id>/', gateway_views.gateways_by_project, name='gateways-by-project'),

    #---------------------- E-Keys ---------------------
    #path('ekeys/', views.ekeys, name='ekeys'),
    #---------------------- Tests ----------------------
    path('thanks/', views.thanks),
    path('check-error/', views.check_error),
    #---------------------- AUTO -----------------------
    path('autosave_field/', auto_views.autosave_field, name='autosave_field'),
    path('autoremove_obj/', auto_views.autoremove_obj, name='autoremove_obj'),
]

