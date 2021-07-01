#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [ 
    path('', views.index, name='web-index'),
    path('projects/', views.projects, name='projects'),
    path('channels/', views.channels, name='channels'),
    path('companies/', views.companies, name='companies'),
]

