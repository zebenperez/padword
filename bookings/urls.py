from django.urls import include, path, re_path
from django.contrib import admin
from bookings import views

urlpatterns = [ 
    #--------------------- Forms --------------------
    path('forms/', views.forms, name='forms'),
    path('forms/project-<slug:project_id>/', views.forms_by_project, name='forms-by-project'),
    path('forms/search/', views.form_search, name='form-search'),

    path('forms/edit/', views.form_edit, name='form-edit'),
    path('forms/edit/<int:form_id>/', views.form_edit, name='form-edit'),
    path('forms/edit/category-<slug:category_uuid>/', views.form_edit, name='form-edit-category'),
    path('forms/form/', views.form_form, name='form-form'),

    path('forms/remove/', views.form_remove, name='form-remove'),
    path('forms/remove/<int:form_id>/', views.form_remove, name='form-remove'),
    path('forms/add-image/', views.form_add_image, name='form-add-image'),
    path('forms/remove-image/', views.form_remove_image, name='form-remove-image'),

    path('channel/add/', views.channel_add, name='channel-add'),
    path('channel/remove/', views.channel_remove, name='channel-remove'),

    path('field/add/', views.field_add, name='field-add'),
    path('field/remove/', views.field_remove, name='field-remove'),

    path('block/add/', views.block_add, name='block-add'),
    path('block/remove/', views.block_remove, name='block-remove'),

    #------------- Bookings --------------#
	path('bookings/', views.bookings, name='bookings'),
	path('bookings_by_form/<int:form_id>/', views.bookings_by_form, name='bookings-by-form'),
	path('bookings_by_project/<int:project_id>/', views.bookings_by_project, name='bookings-by-project'),
    path('bookings/search/', views.bookings_search, name='bookings-search'),

	path('my-bookings/<slug:device_uuid>/', views.bookings_by_device, name='my-bookings'),

	#path('booking-new/<int:form_id>/', views.booking_new, name='booking-new'),
	#path('booking-new/<int:form_id>/<int:device_id>/', views.booking_new, name='booking-new'),
	path('booking-new/<slug:form_uuid>/', views.booking_new, name='booking-new'),
	path('booking-new/<slug:form_uuid>/<slug:device_uuid>/', views.booking_new, name='booking-new'),
	path('booking-edit/<int:fi_id>/', views.booking_edit, name='booking-edit'),
	path('booking-edit/<int:fi_id>/<int:ro>/', views.booking_edit, name='booking-edit'),
	path('booking-remove/<int:fi_id>/', views.booking_remove, name='booking-remove'),
	path('booking-log/<int:fi_id>/', views.booking_log, name='booking-log'),
	path('booking-send/<int:fi_id>/', views.booking_send, name='booking-send'),
    path('status-form/', views.status_form, name='status-form'),
	path('change-status/', views.change_status, name='change-status'),

	path('autosave-form-field/', views.autosave_form_field, name='autosave-form-field'),
	#path('autosave-field/', auto_views.autosave_field, name='bookings-autosave-field'),
	path('get-block/', views.get_block, name='get-block'),
	path('new-row/', views.new_row, name='new-row'),
	path('remove-row/', views.remove_row, name='remove-row'),
	path('autoupload/', views.autoupload, name='autoupload'),
	path('remove-file/', views.remove_file, name='remove-file'),
	path('autocomplete/', views.autocomplete, name='autocomplete'),

        #------- Shopping -----------#
        path('shopping/add-to-cart/', views.item_to_shopping_cart, name='item-to-shopping-cart'),
        path('shopping/view-cart/', views.view_shopping_cart, name='view-shopping-cart'),


	path('test/', views.test, name='booking-test'),
]

