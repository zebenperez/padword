from django.urls import include, path, re_path
from django.contrib import admin
from bookings import views, form_views as fv, guest_views as gv

urlpatterns = [ 
    #--------------------- Forms --------------------
    path('forms/', fv.forms, name='forms'),
    path('forms/project-<slug:project_id>/', fv.forms_by_project, name='forms-by-project'),
    path('forms/search/', fv.form_search, name='form-search'),

    path('forms/edit/', fv.form_edit, name='form-edit'),
    path('forms/edit/<int:form_id>/', fv.form_edit, name='form-edit'),
    path('forms/edit/category-<slug:category_uuid>/', fv.form_edit, name='form-edit-category'),
    path('forms/form/', fv.form_form, name='form-form'),

    path('forms/remove/', fv.form_remove, name='form-remove'),
    path('forms/remove/<int:form_id>/', fv.form_remove, name='form-remove'),
    path('forms/add-image/', fv.form_add_image, name='form-add-image'),
    path('forms/remove-image/', fv.form_remove_image, name='form-remove-image'),
    path('forms/add-logo/', fv.form_add_logo, name='form-add-logo'),
    path('forms/remove-logo/', fv.form_remove_logo, name='form-remove-logo'),
    path('forms/add-qr/', fv.form_add_qr, name='form-add-qr'),
    path('forms/remove-qr/', fv.form_remove_qr, name='form-remove-qr'),

    path('channel/add/', fv.channel_add, name='channel-add'),
    path('channel/remove/', fv.channel_remove, name='channel-remove'),

    path('field/add/', fv.field_add, name='field-add'),
    path('field/remove/', fv.field_remove, name='field-remove'),

    path('block/add/', fv.block_add, name='block-add'),
    path('block/remove/', fv.block_remove, name='block-remove'),

    #------------- Bookings --------------#
    path('login/', views.login, name='login'),

    path('bookings/', views.bookings, name='bookings'),
    path('bookings_by_form/<int:form_id>/', views.bookings_by_form, name='bookings-by-form'),
    path('bookings_by_project/<int:project_id>/', views.bookings_by_project, name='bookings-by-project'),
    path('booking-refresh/<int:obj_id>/', views.booking_refresh, name='booking-refresh'),
    path('booking-refresh/', views.booking_refresh, name='booking-refresh'),

    path('bookings/search/', views.bookings_search, name='bookings-search'),
    path('bookings/search/page/', views.bookings_page, name='bookings-page'),
    path('bookings/notifications/', views.bookings_notifications, name='bookings-notif'),
    path('booking-preview/<slug:form_uuid>/', views.booking_preview, name='booking-preview'),
    #path('booking-view/<int:fi_id>/', views.booking_view, name='booking-view'),
    path('booking-view/', views.booking_view, name='booking-view'),
    path('booking-log/<int:fi_id>/', views.booking_log, name='booking-log'),
    path('status-form/', views.status_form, name='status-form'),
    path('change-status/', views.change_status, name='change-status'),

    #------------- Bookings Guests --------------#
    path('guest-access/<slug:form_uuid>/', gv.guest_access, name='guest-access'),
    path('guest-access-bookings/<slug:project_uuid>/', gv.guest_access_bookings, name='guest-access-bookings'),

    path('guest-form-login/', gv.guest_form_login, name='guest-form-login'),
    path('guest-form-login/<slug:form_uuid>/', gv.guest_form_login, name='guest-form-login'),
    path('booking-new-guest/', gv.booking_new_guest, name='booking-new-guest'),
    #path('booking-new-device/<slug:form_uuid>/datos/', gv.booking_new_device, name='booking-new-device'),
    path('booking-new-device/', gv.booking_new_device, name='booking-new-device'),
    path('booking-new/<slug:form_uuid>/', gv.booking_new, name='booking-new'),

    #path('booking-send/<int:fi_id>/', gv.booking_send, name='booking-send'),
    #path('booking-remove/<int:fi_id>/', gv.booking_remove, name='booking-remove'),
    path('booking-send/', gv.booking_send, name='booking-send'),
    path('booking-remove/', gv.booking_remove, name='booking-remove'),

    path('my-bookings/', gv.bookings_by_guest, name='my-bookings'),
    path('my-bookings/<slug:project_uuid>/', gv.bookings_by_guest, name='my-bookings'),
    #path('booking-view/<int:fi_id>/', gv.booking_view, name='booking-guest-view'),
    path('booking-guest-view/', gv.booking_view, name='booking-guest-view'),

    path('autosave-form-field/', gv.autosave_form_field, name='autosave-form-field'),
    path('get-block/', gv.get_block, name='get-block'),
    path('new-row/', gv.new_row, name='new-row'),
    path('remove-row/', gv.remove_row, name='remove-row'),
    path('autoupload/', gv.autoupload, name='autoupload'),
    path('remove-file/', gv.remove_file, name='remove-file'),
    path('autocomplete/', gv.autocomplete, name='autocomplete'),
    path('select-item/', gv.select_item, name='select-item'),

    path('close/', gv.close, name='close-window'),
    path('close-window/', gv.close_window, name='close-spa'),

    #path('booking-new/<slug:form_uuid>/<slug:device_imei>/', views.booking_new, name='booking-new'),
    #path('booking-new/<slug:form_uuid>/<slug:device_imei>/<slug:room_number>/<slug:guest_name>/<slug:guest_surname>/', views.booking_new, name='booking-new'),

    #------- Shopping -----------#
    path('shopping/add-to-cart/', gv.item_to_shopping_cart, name='item-to-shopping-cart'),
    path('shopping/remove-generic-from-cart/', gv.remove_generic_item_from_shopping_cart, name='remove-generic-item-shopping-cart'),
    path('shopping/remove-from-cart/', gv.remove_item_from_shopping_cart, name='remove-item-shopping-cart'),
    path('shopping/view-cart/', gv.view_shopping_cart, name='view-shopping-cart'),
    path('shopping/get-price/', gv.get_price_shopping_cart, name='get-price-shopping-cart'),
    path('shopping/show-category/<int:form_id>/<slug:cat_id>/', gv.show_category_shopping_cart, name='show-category-shopping-cart'),
    path('shopping/show-category/', gv.show_category_shopping_cart, name='show-category-shopping-cart'),
    path('shopping/comments/', gv.item_shopping_cart_comment, name='item-shopping-cart-comment'),

    path('test/', views.test, name='booking-test'),
]

