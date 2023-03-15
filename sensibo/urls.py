#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [ 
    path('device-by-project/<int:project_id>/', views.devices_by_project, name='sensibo-device-by-project'),
    path('device-switch/', views.device_switch, name='sensibo-device-switch'),
    path('device-set-state/', views.device_set_state, name='sensibo-device-set-state'),
    path('device-save-room/', views.device_save_room, name='sensibo-device-save-room'),
    path('device-by-project2/', views.devices_by_project2, name='sensibo-device-by-project2'),
    path('device-switch-project/', views.device_switch_project, name='sensibo-device-switch-project'),
    path('device-set-state-project/', views.device_set_state_project, name='sensibo-device-set-state-project'),
]

