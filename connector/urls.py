from django.urls import path
from . import views, camera_views

urlpatterns = [ 
    #--------------------- AVANTIO --------------------
    path('avantio/get-booking-list/<slug:project_uuid>/', views.avantio_get_booking_list, name='avantio-get-booking-list'),
    path('avantio/get-booking-notif/<slug:project_uuid>/', views.avantio_get_booking_notif, name='avantio-get-booking-notif'),
    path('avantio/send-link/<slug:project_uuid>/<slug:guest_uuid>/', views.avantio_send_link, name='avantio-send-link'),

    #--------------------- AVAIBOOK --------------------
    path('avaibook/get-booking-list/<slug:project_uuid>/', views.avaibook_get_booking_list, name='avaibook-get-booking-list'),
    path('avaibook/get-accommodation-list/<slug:project_uuid>/', views.avaibook_get_accommodation_list, name='avaibook-get-accommodation-list'),
    path('avaibook/get-booking/', views.avaibook_get_booking, name='avaibook-get-booking'),

    #--------------------- WINHOTEL --------------------
    path('winhotel/get-booking-list/<slug:project_uuid>/', views.winhotel_get_booking_list, name='winhotel-get-booking-list'),
    path('winhotel/get-day-booking-list/', views.winhotel_get_day_booking_list, name='winhotel-get-day-booking-list'),
    path('winhotel/import-items/<slug:project_uuid>/', views.winhotel_import_items, name='winhotel-import-items'),

    #--------------------- MEWS --------------------
    path('mews/get-booking-list/<slug:project_uuid>/', views.mews_get_booking_list, name='mews-get-booking-list'),
    path('mews/cancel-booking-list/<slug:project_uuid>/', views.mews_cancel_booking_list, name='mews-cancel-booking-list'),

    #--------------------- CLOUDBEDS --------------------
    path('cloudbeds/get-booking-list/<slug:project_uuid>/', views.cloudbeds_get_booking_list, name='cloudbeds-get-booking-list'),
    path('cloudbeds/get-room-list/<slug:project_uuid>/', views.cloudbeds_get_room_list, name='cloudbeds-get-room-list'),
    path('cloudbeds/set-webhooks/', views.cloudbeds_set_webhooks, name='cloudbeds-set-webhooks'),
    path('cloudbeds/webhook/', views.cloudbeds_webhook, name='cloudbeds-webhook'),

    #--------------------- PAYTEF --------------------
    path('paytef/get-config/<slug:project_uuid>/', views.paytef_get_config, name='paytef-get-config'),

    #--------------------- ZKTECO --------------------
    path('zkteco/webhook/', views.zkteco_webhook, name='zkteco-webhook'),

    #--------------------- CRON --------------------
    path('cron-log/', views.cron_log, name='cron-log'),
    path('avantio-log/', views.avantio_log, name='avantio-log'),
    path('avaibook-log/', views.avaibook_log, name='avaibook-log'),
    path('winhotel-log/', views.winhotel_log, name='winhotel-log'),
    path('cloudbeds-log/', views.cloudbeds_log, name='cloudbeds-log'),

    #--------------------- CAMERA --------------------
    path('car/plates/<slug:project_uuid>/', camera_views.car_plates, name='car_plates'),

    #--------------------- ACCESS CONTROL --------------------
    path('access-control/<slug:project>/<slug:card>/', views.access_control, name='access-control'),

    #--------------------- TEST --------------------
    path('test-email/', views.test_email, name='test-email'),
]

