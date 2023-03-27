from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from padword.commons import show_exc, get_or_none, new_ui_slug
from padword.decorators import group_required
from guest.models import Guest
from .avantio_lib import ShAvantio
from .models import ProjectAvantioUser



'''
    Avantio
'''
@group_required("admins")
def avantio_get_booking_list(request, project_uuid):
    try:
        pau = ProjectAvantioUser.objects.filter(project_uuid=project_uuid).first()
        if pau != None:
            av = ShAvantio(pau.username, pau.password)
            booking_list = av.get_booking_list()
            print(booking_list)
            for booking in booking_list:
                guest = Guest.objects.filter(ext_id=booking.localizator).first()
                if guest == None:
                    guest = Guest(UUID = new_ui_slug(Guest), ext_id=booking.localizator)
                    guest.name = booking.client.name
                    guest.surname = booking.client.surname
                    #guest.language = booking.client.languaje
                    #guest.room = booking.client.room
                    #guest.save()

        #return HttpResponse(booking_list)
        return render(request, 'avantio/booking-list.html', {'booking_list': booking_list})
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


