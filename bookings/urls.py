from django.urls import include, path, re_path
from django.contrib import admin
from bookings import views

urlpatterns = [ 
    #--------------------- Forms --------------------
    path('forms/', views.forms, name='forms'),
    path('forms/search/', views.form_search, name='form-search'),
    path('forms/form/', views.form_form, name='form-form'),
    path('forms/remove/', views.form_remove, name='form-remove'),
    path('channel/add/', views.channel_add, name='channel-add'),
    path('channel/remove/', views.channel_remove, name='channel-remove'),

    #------------- Bookings --------------#
	path('bookings/<int:form_id>/', views.bookings, name='bookings'),
	path('booking-new/<int:form_id>/', views.booking_new, name='booking-new'),
	path('booking-edit/<int:fi_id>/', views.booking_edit, name='booking-edit'),
	path('booking-edit/<int:fi_id>/<int:ro>/', views.booking_edit, name='booking-edit'),
	path('booking-remove/<int:fi_id>/', views.booking_remove, name='booking-remove'),
	path('booking-log/<int:fi_id>/', views.booking_log, name='booking-log'),
	path('set-status/<int:fi_id>/<slug:status>/', views.set_status, name='set-status'),
    path('status-form/', views.status_form, name='status-form'),
	path('change-status/', views.change_status, name='change-status'),

	path('autosave-form-field/', views.autosave_form_field, name='autosave-form-field'),
	path('get-block/', views.get_block, name='get-block'),
	path('new-row/', views.new_row, name='new-row'),
	path('remove-row/', views.remove_row, name='remove-row'),
	path('autoupload/', views.autoupload, name='autoupload'),
	path('remove-file/', views.remove_file, name='remove-file'),
	path('autocomplete/', views.autocomplete, name='autocomplete'),
]

