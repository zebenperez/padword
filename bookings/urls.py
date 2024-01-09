from django.urls import include, path, re_path
from django.contrib import admin
from bookings import views, form_views as fv, guest_views as gv, guest_sensibo_views as gsv
from bookings import tpv_views as tpv, tpv_orders_views as tpv_orders, tpv_mobile_views as tpv_mob, tpv_orders_daily_views as tpv_orders_daily
from bookings import tpv_cash_views as tpv_cash

urlpatterns = [ 
    #--------------------- Forms --------------------
    path('forms/', fv.forms, name='forms'),
    path('forms/project-<slug:project_id>/', fv.forms_by_project, name='forms-by-project'),
    path('forms/search/', fv.form_search, name='form-search'),

    path('forms/edit/', fv.form_edit, name='form-edit'),
    path('forms/edit/<int:form_id>/', fv.form_edit, name='form-edit'),
    path('forms/change-active/<int:form_id>/', fv.form_change_active, name='form-change-active'),
    path('forms/edit/category/', fv.form_edit_category, name='form-edit-category2'),
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

    path('forms/new_email', fv.new_email, name="form-new-email"),
    path('forms/remove_email', fv.remove_email, name="form-remove-email"),

    path('forms/new_timetable', fv.new_timetable, name="form-new-timetable"),
    path('forms/remove_timetable', fv.remove_timetable, name="form-remove-timetable"),

    path('channel/add/', fv.channel_add, name='channel-add'),
    path('channel/remove/', fv.channel_remove, name='channel-remove'),

    path('field/add/', fv.field_add, name='field-add'),
    path('field/remove/', fv.field_remove, name='field-remove'),

    path('block/add/', fv.block_add, name='block-add'),
    path('block/remove/', fv.block_remove, name='block-remove'),

    #------------- Bookings --------------#
    path('login/', views.login, name='login'),

    path('bookings/', views.bookings, name='bookings'),
    #path('bookings_by_form/<int:form_id>/', views.bookings_by_form, name='bookings-by-form'),
    path('booking-refresh/<int:obj_id>/', views.booking_refresh, name='booking-refresh'),
    path('booking-refresh/', views.booking_refresh, name='booking-refresh'),
    path('booking-refresh-status/<int:obj_id>/', views.booking_refresh_status, name='booking-refresh-status'),
    path('booking-refresh-status/', views.booking_refresh_status, name='booking-refresh-status'),

    path('bookings/search/', views.bookings_search, name='bookings-search'),
    path('bookings/search/page/', views.bookings_page, name='bookings-page'),
    #path('bookings/notifications/', views.bookings_notifications, name='bookings-notif'),
    path('bookings/notifications/<slug:ini_date>/<slug:end_date>/', views.bookings_notifications, name='bookings-notif'),
    path('booking-preview/<slug:form_uuid>/', views.booking_preview, name='booking-preview'),
    #path('booking-view/<int:fi_id>/', views.booking_view, name='booking-view'),
    path('booking-view/', views.booking_view, name='booking-view'),
    path('booking-log/<int:fi_id>/', views.booking_log, name='booking-log'),
    path('status-form/', views.status_form, name='status-form'),
    path('change-status/', views.change_status, name='change-status'),
    path('booking/cancel/', views.booking_cancel, name='booking-cancel'),

    #------------- Bookings Project --------------#
    #path('bookings_by_project/<int:project_id>/', views.bookings_by_project, name='bookings-by-project'),
    path('bookings_by_project/', views.bookings_by_project, name='bookings-by-project'),
    path('bookings/project/search/', views.bookings_pr_search, name='bookings-pr-search'),
    path('bookings/project/search/page/', views.bookings_pr_page, name='bookings-pr-page'),

    #------------- Bookings Project Live --------------#
    path('bookings/live/project/', views.bookings_live_by_project, name='bookings-live-by-project'),

    #------------- Bookings Category --------------#
    #path('bookings_by_category/<int:category_id>/', views.bookings_by_category, name='bookings-by-category'),
    path('bookings_by_category/', views.bookings_by_category, name='bookings-by-category'),
    path('bookings/category/search/', views.bookings_cat_search, name='bookings-cat-search'),
    path('bookings/category/search/page/', views.bookings_cat_page, name='bookings-cat-page'),

    path('forms/edit/category/user/', views.form_edit_category_user, name='form-edit-category-user'),

    #------------- Bookings Guests --------------#
    path('guest-access/<slug:category_uuid>/', gv.guest_access, name='guest-access'),
    path('guest-access-auto/<slug:guest_uuid>/', gv.guest_access_auto, name='guest-access-auto'),
    #path('guest-access-anonymous/<slug:category_uuid>/', gv.guest_access_anonymous, name='guest-access-anonymous'),
    path('guest-set-lang/', gv.set_guest_language, name='guest-set-lang'),
    #path('guest-set-lang/<slug:category_uuid>/<str:lang>/', gv.set_guest_language, name='guest-set-lang'),
    #path('guest-access/<slug:form_uuid>/', gv.guest_access, name='guest-access'),
    #path('guest-access-bookings/<slug:project_uuid>/', gv.guest_access_bookings, name='guest-access-bookings'),
    #path('guest-access-pwa/<slug:project_uuid>/', gv.guest_access_pwa, name='guest-access-pwa'),
    #path('guest-access-pwa/<slug:category_uuid>/<str:lang>/', gv.guest_access_pwa, name='guest-access-pwa'),
    #path('guest-access-pwa/<slug:category_uuid>/<str:lang>/', gv.set_guest_language, name='guest-access-pwa'),
    #path('guest-access-pwa/<slug:category_uuid>/', gv.guest_access_pwa, name='guest-access-pwa'),
    #path('reload-top-menu/<slug:category_uuid>/', gv.reload_top_menu, name='reload-top-menu'),

    path('guest-form-login/', gv.guest_form_login, name='guest-form-login'),
    #path('guest-form-login/<slug:form_uuid>/', gv.guest_form_login, name='guest-form-login'),
    path('booking-new-guest/', gv.booking_new_guest, name='booking-new-guest'),
    #path('booking-new-device/<slug:form_uuid>/datos/', gv.booking_new_device, name='booking-new-device'),
    #path('booking-new-device/', gv.booking_new_device, name='booking-new-device'),
    #path('booking-new/<slug:form_uuid>/', gv.booking_new, name='booking-new'),

    #path('booking-send/<int:fi_id>/', gv.booking_send, name='booking-send'),
    #path('booking-remove/<int:fi_id>/', gv.booking_remove, name='booking-remove'),
    path('booking-send/', gv.booking_send, name='booking-send'),
    path('booking-remove/', gv.booking_remove, name='booking-remove'),
    path('booking-payment-type/', gv.booking_payment_type, name='booking-payment-type'),

    path('my-bookings/', gv.bookings_by_guest, name='my-bookings'),
    path('my-bookings/<slug:project_uuid>/', gv.bookings_by_guest, name='my-bookings'),
    #path('booking-view/<int:fi_id>/', gv.booking_view, name='booking-guest-view'),
    path('booking-guest-view/', gv.booking_view, name='booking-guest-view'),

    path('my-notifications/', gv.notifications_by_guest, name='my-notifications'),
    path('notification-view/', gv.notification_view, name='notification-view'),
    path('notifications-not-readed/', gv.notifications_not_readed, name='notifications-not-readed'),
    path('notifications-check/', gv.notifications_check, name='notifications-check'),

    path('my-messages/', gv.messages_by_guest, name='my-messages'),

    path('autosave-form-field/', gv.autosave_form_field, name='autosave-form-field'),
    path('get-block/', gv.get_block, name='get-block'),
    path('new-row/', gv.new_row, name='new-row'),
    path('remove-row/', gv.remove_row, name='remove-row'),
    path('autoupload/', gv.autoupload, name='autoupload'),
    path('remove-file/', gv.remove_file, name='remove-file'),
    path('autocomplete/', gv.autocomplete, name='autocomplete'),
    path('select-item/', gv.select_item, name='select-item'),

    path('bookings/show-item/', gv.show_item, name='show-item'),

    path('close/', gv.close, name='close-window'),
    path('close-window/', gv.close_window, name='close-spa'),

    path('guests/notifications/<slug:form_id>/', gv.guest_notifications, name='guest-notif'),

    path('guests/open-lock/', gv.open_lock, name='open-lock'),

    path('guests/band-scan/', gv.band_scan, name='band-scan'),

    #path('booking-new/<slug:form_uuid>/<slug:device_imei>/', views.booking_new, name='booking-new'),
    #path('booking-new/<slug:form_uuid>/<slug:device_imei>/<slug:room_number>/<slug:guest_name>/<slug:guest_surname>/', views.booking_new, name='booking-new'),

    #------------- Bookings Sensibo Guests --------------#
    path('guest-show-sensibo-menu/', gsv.show_sensibo_menu, name='show-sensibo-menu'),
    path('guest-sensibo-device-switch/', gsv.device_switch, name='guest-sensibo-device-switch'),
    path('guest-sensibo-device-set-state/', gsv.device_set_state, name='guest-sensibo-device-set-state'),

    #------- Shopping -----------#
    path('shopping/add-to-cart/', gv.item_to_shopping_cart, name='item-to-shopping-cart'),
    path('shopping/remove-generic-from-cart/', gv.remove_generic_item_from_shopping_cart, name='remove-generic-item-shopping-cart'),
    path('shopping/remove-from-cart/', gv.remove_item_from_shopping_cart, name='remove-item-shopping-cart'),
    path('shopping/view-cart/<slug:par>/', gv.view_shopping_cart, name='view-shopping-cart'),
    path('shopping/view-cart/', gv.view_shopping_cart, name='view-shopping-cart'),
    path('shopping/get-price/', gv.get_price_shopping_cart, name='get-price-shopping-cart'),
    #path('shopping/show-category/<int:form_id>/<slug:cat_id>/', gv.show_category_shopping_cart, name='show-category-shopping-cart'),
    path('shopping/show-category/', gv.show_category_shopping_cart, name='show-category-shopping-cart'),
    path('shopping/comments/', gv.item_shopping_cart_comment, name='item-shopping-cart-comment'),
    path('shopping/show-category-menu/<slug:cat_id>/<str:back>/', gv.show_category_menu, name='show-category-menu'),
    #path('shopping/show-category-menu-lang/<slug:cat_id>/<str:lang>/', gv.show_category_menu, name='show-category-menu-lang'),
    path('shopping/show-category-menu/<slug:cat_id>/', gv.show_category_menu, name='show-category-menu'),
    #path('shopping/show-category-menu/<int:form_id>/<slug:cat_id>/', gv.show_category_menu, name='show-category-menu'),
    path('shopping/show-category-menu/', gv.show_category_menu, name='show-category-menu'),
    path('shopping/show-key-menu/', gv.show_key_menu, name='show-key-menu'),


    #------------- TPV --------------#
    path('tpv-access/<slug:project_uuid>/', tpv.tpv_access, name='tpv-access'),
    path('tpv-login/', tpv.tpv_login, name='tpv-login'),
    path('tpv-login-form/', tpv.tpv_login_form, name='tpv-login-form'),
    path('tpv-close/', tpv.tpv_close, name='tpv-close'),

    path('tpv-index/<slug:project_uuid>/', tpv.tpv_index, name='tpv-index'),
    path('tpv-ticket/', tpv.tpv_ticket, name='tpv-ticket'),
    path('tpv-set-pos/', tpv.tpv_set_pos, name='tpv-set-pos'),
    path('tpv-change-pos/', tpv.tpv_change_pos, name='tpv-change-pos'),
    path('tpv-set-table/', tpv.tpv_set_table, name='tpv-set-table'),
    path('tpv-change-table/', tpv.tpv_change_table, name='tpv-change-table'),
    path('tpv-set-cash/', tpv.tpv_set_cash, name='tpv-set-cash'),
    path('tpv-cash-z/', tpv.cash_z, name='tpv-cash-z'),
    path('tpv-check-band/', tpv.tpv_check_band, name='tpv-check-band'),

    #path('tpv-shopping-cart/', tpv.tpv_shopping_cart, name='tpv-shopping-cart'),
    #path('tpv-category-shopping-cart/', tpv.tpv_category_shopping_cart, name='tpv-category-shopping-cart'),
    path('tpv-add-item/', tpv.tpv_add_item, name='tpv-add-item'),
    #path('tpv-remove-item/', tpv.tpv_remove_item, name='tpv-remove-item'),
    #path('tpv-set-items/', tpv.tpv_set_items, name='tpv-set-items'),

    path('tpv-order-remove/', tpv.tpv_order_remove, name='tpv-order-remove'),
    #path('tpv-order-view/', tpv.tpv_order_view, name='tpv-order-view'),
    path('tpv-order-item-remove/', tpv.tpv_order_item_remove, name='tpv-order-item-remove'),
    path('tpv-order-item-comment/', tpv.tpv_order_item_comment, name='tpv-order-item-comment'),
    #path('tpv-order-payment/', tpv.tpv_order_payment, name='tpv-order-payment'),
    path('tpv-order-send/', tpv.tpv_order_send, name='tpv-order-send'),

    path('tpv-orders-by-waiter/', tpv.orders_by_waiter, name='tpv-orders-by-waiter'),
    path('tpv-order-details/', tpv.order_details, name='tpv-order-details'),

    #------------- TPV MOBILE --------------#
    path('tpv-mob-access/<slug:project_uuid>/', tpv_mob.tpv_access, name='tpv-mob-access'),
    path('tpv-mob-access/<slug:project_uuid>/<slug:mobile>', tpv_mob.tpv_access, name='tpv-mob-access'),
    path('tpv-mob-login/', tpv_mob.tpv_login, name='tpv-mob-login'),
    path('tpv-mob-login-form/', tpv_mob.tpv_login_form, name='tpv-mob-login-form'),
    path('tpv-mob-close/', tpv_mob.tpv_close, name='tpv-mob-close'),

    path('tpv-mob-index/<slug:project_uuid>/', tpv_mob.tpv_index, name='tpv-mob-index'),
    path('tpv-mob-ticket/', tpv_mob.tpv_ticket, name='tpv-mob-ticket'),
    path('tpv-mob-set-pos/', tpv_mob.tpv_set_pos, name='tpv-mob-set-pos'),
    path('tpv-mob-change-pos/', tpv_mob.tpv_change_pos, name='tpv-mob-change-pos'),
    path('tpv-mob-set-table/', tpv_mob.tpv_set_table, name='tpv-mob-set-table'),
    path('tpv-mob-change-table/', tpv_mob.tpv_change_table, name='tpv-mob-change-table'),
    #path('tpv-mob-set-cash/', tpv_mob.tpv_set_cash, name='tpv-mob-set-cash'),
    path('tpv-mob-check-band/', tpv_mob.tpv_check_band, name='tpv-mob-check-band'),

    path('tpv-mob-item-add/', tpv_mob.tpv_item_add, name='tpv-mob-item-add'),
    path('tpv-mob-item-remove/', tpv_mob.tpv_item_remove, name='tpv-mob-item-remove'),

    #path('tpv-add-item/', tpv.tpv_add_item, name='tpv-add-item'),

    #path('tpv-order-remove/', tpv.tpv_order_remove, name='tpv-order-remove'),
    #path('tpv-order-item-remove/', tpv.tpv_order_item_remove, name='tpv-order-item-remove'),
    #path('tpv-order-item-comment/', tpv.tpv_order_item_comment, name='tpv-order-item-comment'),
    #path('tpv-order-send/', tpv.tpv_order_send, name='tpv-order-send'),

    #path('tpv-orders-by-waiter/', tpv.orders_by_waiter, name='tpv-orders-by-waiter'),
    #path('tpv-order-details/', tpv.order_details, name='tpv-order-details'),

    #------------- TPV Orders --------------#
    path('orders_by_project/', tpv_orders.orders_by_project, name='orders-by-project'),
    path('orders/project/search/', tpv_orders.orders_search, name='orders-search'),
    path('orders/project/search/page/', tpv_orders.orders_page, name='orders-page'),


    path('fix-uuid/', views.fix_uuid, name='booking-fix-uuid'),
    path('test/', views.test, name='booking-test'),

    #------------- TPV Orders Daily --------------#
    path('orders_daily/orders-daily/', tpv_orders_daily.orders_daily_by_project, name='orders-daily-by-project'),
    path('orders_daily/search/', tpv_orders_daily.orders_daily_search, name='orders-daily-search'),
    path('orders_daily/summary/', tpv_orders_daily.orders_daily_summary, name='orders-daily-summary'),
    path('orders_daily/remove/', tpv_orders_daily.orders_daily_remove, name='orders-daily-remove'),
    #path('orders_daily/z/', tpv_orders_daily.orders_z, name='orders-z'),

    #------------- TPV Cash --------------#
    path('tpv-cash/index/', tpv_cash.cash_by_project, name='cash-by-project'),
    path('tpv-cash/search/', tpv_cash.cash_search, name='cash-search'),
    path('tpv-cash/new/', tpv_cash.cash_new, name='cash-new'),
    path('tpv-cash/remove/', tpv_cash.cash_remove, name='cash-remove'),
    path('tpv-cash/z/', tpv_cash.cash_z, name='cash-z'),
    path('tpv-cash/print-z/<int:obj_id>', tpv_cash.print_z, name='cash-z-print'),
 
]

