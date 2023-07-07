from django.urls import path
from . import views

urlpatterns = [ 
    path('avantio/get-booking-list/<slug:project_uuid>/', views.avantio_get_booking_list, name='avantio-get-booking-list'),
    path('avantio/get-booking-notif/<slug:project_uuid>/', views.avantio_get_booking_notif, name='avantio-get-booking-notif'),
    path('avantio/send-link/<slug:project_uuid>/<slug:guest_uuid>/', views.avantio_send_link, name='avantio-send-link'),
    path('cron-log/', views.cron_log, name='cron-log'),
]

