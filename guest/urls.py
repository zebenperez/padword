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
    path('guests/page/<int:page>/', views.guest_pagination, name='guest-page'),

    #--------------------- GUESTS --------------------
    path('', views.index, name='device-index'),
    path('devices/', views.devices, name='guest-devices'),
    path('devices/search/', views.device_search, name='guest-device-search'),
    path('devices/form/', views.device_form, name='guest-device-form'),
    path('devices/room/', views.device_room, name='guest-device-room'),
    path('devices/remove/', views.device_remove, name='guest-device-remove'),
    path('devices/page/<int:page>/', views.device_pagination, name='guest-device-page'),

]

