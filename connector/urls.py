from django.urls import path
from . import views

urlpatterns = [ 
    #--------------------- AVANTIO --------------------
    path('avantio/get-booking-list/<slug:project_uuid>/', views.avantio_get_booking_list, name='avantio-get-booking-list'),
    path('avantio/get-booking-notif/<slug:project_uuid>/', views.avantio_get_booking_notif, name='avantio-get-booking-notif'),
    path('avantio/send-link/<slug:project_uuid>/<slug:guest_uuid>/', views.avantio_send_link, name='avantio-send-link'),

    #--------------------- AVAIBOOK --------------------
    path('avaibook/get-booking-list/<slug:project_uuid>/', views.avaibook_get_booking_list, name='avaibook-get-booking-list'),

    #--------------------- CRON --------------------
    path('cron-log/', views.cron_log, name='cron-log'),

    #--------------------- TEST --------------------
    path('test-email/', views.test_email, name='test-email'),
]

