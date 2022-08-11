#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views, auto_views

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
    path('locks/', views.locks, name='locks'),
    path('locks/search/', views.lock_search, name='lock-search'),
    path('locks/form/', views.lock_form, name='lock-form'),
    path('locks/remove/', views.lock_remove, name='lock-remove'),
    path('locks/get-all-passcodes/', views.lock_get_all_passcodes, name='lock-get-all-passcodes'),

    #---------------------- E-Keys ---------------------
    #path('ekeys/', views.ekeys, name='ekeys'),
    #---------------------- Tests ----------------------
    path('thanks/', views.thanks),
    path('check-error/', views.check_error),
    #---------------------- AUTO -----------------------
    path('autosave_field/', auto_views.autosave_field, name='autosave_field'),
    path('autoremove_obj/', auto_views.autoremove_obj, name='autoremove_obj'),
]

