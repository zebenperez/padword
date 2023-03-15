from django.urls import path
from . import views

urlpatterns = [ 
    path('avantio/get-booking-list/', views.avantio_get_booking_list, name='avantio-get-booking-list'),
]

