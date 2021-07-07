#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [ 
    path('', views.index, name='web-index'),
    #--------------------- Projects --------------------
    path('projects/', views.projects, name='projects'),
    path('projects/search/', views.project_search, name='project-search'),
    #--------------------- Channels --------------------
    path('channels/<slug:project_id>/', views.channels, name='channels'),
    path('channels/', views.channels, name='channels'),
    path('channels/search/', views.channel_search, name='channel-search'),
    #--------------------- Companies --------------------
    path('companies/', views.companies, name='companies'),
    path('companies/search/', views.company_search, name='company-search'),
    #--------------------- Devices --------------------
    path('devices/by-project/<slug:project_id>/', views.devices, name='devices-by-project'),
    path('devices/by-channel/<slug:channel_id>/', views.devices, name='devices-by-channel'),
    path('devices/', views.devices, name='devices'),
    path('devices/search/', views.device_search, name='device-search'),
]

