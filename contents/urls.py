#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [ 
    path('', views.index, name='contents-index'),
    path('', views.index, name='category-form'),
    path('categories/search/', views.category_search, name='category-search'),
    path('categories/project-<slug:project_id>/', views.categories_by_project, name='categories-by-project'),
    path('tree/category-<slug:category_id>/', views.category_tree, name='items-by-category'),
]

