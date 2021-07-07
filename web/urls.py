#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [ 
    path('', views.index, name='web-index'),
    #--------------------- Projects --------------------
    path('projects/<int:company_id>/', views.projects, name='projects-by-company'),
    path('projects/', views.projects, name='projects'),
    path('projects/search/', views.project_search, name='project-search'),
    #--------------------- Channels --------------------
    path('channels/project-<slug:project_id>/', views.channels, name='channels-by-project'),
    path('channels/company-<slug:company_id>/', views.channels, name='channels-by-company'),
    path('channels/', views.channels, name='channels'),
    path('channels/search/', views.channel_search, name='channel-search'),
    #--------------------- Companies --------------------
    path('companies/', views.companies, name='companies'),
    path('companies/search/', views.company_search, name='company-search'),
    #--------------------- Devices --------------------
    path('devices/project-<int:project_id>/', views.devices, name='devices-by-project'),
    path('devices/channel-<int:channel_id>/', views.devices, name='devices-by-channel'),
    path('devices/company-<int:company_id>/', views.devices, name='devices-by-company'),
    path('devices/', views.devices, name='devices'),
    path('devices/search/', views.device_search, name='device-search'),
]

