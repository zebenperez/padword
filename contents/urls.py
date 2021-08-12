#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.urls import path
from . import views, auto_views

urlpatterns = [ 
    path('', views.index, name='contents-index'),
    path('categories/form/', views.category_form, name='category-form'),
    path('categories/search/', views.category_search, name='category-search'),
    path('categories/project-<slug:project_id>/', views.categories_by_project, name='categories-by-project'),
    path('categories/import/project-<slug:project_uuid>/', views.import_categories, name='import-categories-by-project'),
    path('categories/import/', views.import_categories, name='import-categories-by-project'),
    path('tree/category-<slug:category_id>/', views.category_tree, name='items-by-category'),
    path('categories/change-active-category-<slug:category_id>/', views.category_change_active, name='change-active-category'),
    path('categories/remove-category-<slug:category_id>/', views.category_remove, name='category-remove'),
    #---------------------- AUTO -----------------------
	path('autosave_field/', auto_views.autosave_field, name='autosave_field'),
	path('autoremove_obj/', auto_views.autoremove_obj, name='autoremove_obj'),
]

