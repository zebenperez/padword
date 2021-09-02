#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [ 

    path('', views.users, name='user-index'),
    path('users/', views.users, name='users'),
    path('users/search/', views.user_search, name='user-search'),
    path('users/form/', views.user_form, name='user-form'),
    path('users/remove/', views.user_remove, name='user-remove'),

]

