#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [ 

    path('', views.index, name='guest-index'),
    path('guests/', views.guests, name='guests'),
    path('guests/search/', views.guest_search, name='guest-search'),

]

