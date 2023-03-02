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
    path('categories/clone/', views.category_clone, name='category-clone'),
    path('categories/links/', views.category_links, name='category-links'),
    path('tree/category-<slug:category_id>/', views.category_tree, name='items-by-category'),
    path('categories/change-active-category-<slug:category_id>/', views.category_change_active, name='change-active-category'),
    path('categories/remove-category-<slug:category_id>/', views.category_remove, name='category-remove'),
    path('categories/import-by-file/', views.import_categories_by_file, name='import-categories-by-file'),
    path('categories/add-image/', views.category_add_image, name='category-add-image'),
    path('categories/remove-image/', views.category_remove_image, name='category-remove-image'),
    path('categories/add-image-gallery/', views.category_add_image_gallery, name='category-add-image-gallery'),
    path('categories/remove-image-gallery/', views.category_remove_image_gallery, name='category-remove-image-gallery'),
    path('categories/save_feature', views.save_feature, name="category-save-feature"),
    path('categories/save_payment_type', views.save_payment_type, name="category-save-payment-type"),

    path('categories/categories/', views.categories_by_categories, name='categories-by-categories'),

    path('items/form/', views.item_form, name='item-form'),
    path('items/change-image/', views.item_change_image, name='item-change-image'),
    path('items/change-active-item-<slug:item_id>/', views.item_change_active, name='change-active-item'),
    path('items/remove-item/', views.item_remove, name='item-remove'),
    path('items/get-img/<int:item_id>/', views.item_get_img, name='item-get-img'),
    #path('items/remove-item-<slug:item_id>/', views.item_remove, name='item-remove'),
    path('items/save_allergen', views.save_allergen, name="items-save-allergen"),
    path('items/add-image/', views.item_add_image, name='item-add-image'),
    path('items/remove-image/', views.item_remove_image, name='item-remove-image'),
    path('items/new_extra', views.new_extra, name="items-new-extra"),
    path('items/remove_extra', views.remove_extra, name="items-remove-extra"),
    path('items/add-image-gallery/', views.item_add_image_gallery, name='item-add-image-gallery'),
    path('items/remove-image-gallery/', views.item_remove_image_gallery, name='item-remove-image-gallery'),
    path('items/new_promo', views.new_promo, name="items-new-promo"),
    path('items/remove_promo', views.remove_promo, name="items-remove-promo"),
    path('items/add-banner/', views.item_add_banner, name='item-add-banner'),
    path('items/remove-banner/', views.item_remove_banner, name='item-remove-banner'),
    path('items/change-price/', views.item_change_price, name='item-change-price'),


    #---------------------- AUTO -----------------------
	path('autosave_field/', auto_views.autosave_field, name='autosave_field'),
	path('autosave_field_post/', auto_views.autosave_field_post, name='autosave_field_post'),
	path('autoremove_obj/', auto_views.autoremove_obj, name='autoremove_obj'),
]

