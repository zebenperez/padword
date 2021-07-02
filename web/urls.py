#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [ 
    path('', views.index, name='web-index'),
    #--------------------- Projects --------------------
    path('projects/', views.projects, name='projects'),
    path('projects/search/', views.project_search, name='project-search'),

    path('channels/', views.channels, name='channels'),
    path('companies/', views.companies, name='companies'),
    path('devices/', views.devices, name='devices'),
]

