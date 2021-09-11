#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [ 

    path('', views.index, name='guest-index'),
    path('guests/', views.guests, name='guests'),
    path('guests/search/', views.guest_search, name='guest-search'),
    path('guests/form/', views.guest_form, name='guest-form'),
    path('guests/remove/', views.guest_remove, name='guest-remove'),
    path('guests/page/<int:page>/', views.guest_pagination, name='guest-page'),

]

