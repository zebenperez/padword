from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc 
from padword.decorators import group_required
from .avantio_lib import ShAvantio



'''
    Avantio
'''
@group_required("admins")
def avantio_get_booking_list(request):
    try:
        av = ShAvantio()
        booking_list = av.get_booking_list()
        print(booking_list)

        #return HttpResponse(booking_list)
        return render(request, 'avantio/booking-list.html', {'booking_list': booking_list})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


