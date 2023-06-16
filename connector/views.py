from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext_lazy as _ 

from datetime import datetime, timedelta

from padword.commons import show_exc, get_or_none, new_ui_slug
from padword.decorators import group_required
from guest.models import Guest
from .avantio_lib import ShAvantio
from .models import ProjectAvantioUser


'''
    Avantio
'''
def get_date(date, time, default):
    if date != "" and time != "":
        return datetime.strptime("{} {}".format(date, time), "%Y-%m-%d %H:%M")
    return default + timedelta(days=-1)

def get_dates_range(pau):
    if pau.days > 0:
        start_date = datetime.today()
        end_date = start_date + timedelta(days=pau.days)
    else:
        end_date = datetime.today()
        start_date = end_date + timedelta(days=pau.days)
    return start_date, end_date

@group_required("admins", "projects")
def avantio_get_booking_list(request, project_uuid):
    try:
        err = ""
        pau = ProjectAvantioUser.objects.filter(project_uuid=project_uuid).first()
        if pau != None:
            #if pau.days > 0:
            #    start_date = datetime.today()
            #    end_date = start_date + timedelta(days=pau.days)
            #else:
            #    end_date = datetime.today()
            #    start_date = end_date + timedelta(days=pau.days)
            start_date, end_date = get_dates_range(pau)
            av = ShAvantio(pau.username, pau.password)
            booking_list = av.get_booking_list(start_date, end_date)
            for booking in booking_list:
                #checkin = start_date + timedelta(days=-1)
                #if booking.start_date != "" and booking.start_time != "":
                #    checkin = datetime.strptime("{} {}".format(booking.start_date, booking.start_time), "%Y-%m-%d %H:%M")
                #if booking.end_date != "" and booking.end_time != "":
                #    checkout = datetime.strptime("{} {}".format(booking.end_date, booking.end_time), "%Y-%m-%d %H:%M")
                checkin = get_date(booking.start_date, booking.start_time, start_date)
                if checkin >= start_date and checkin <= end_date:
                    code = "{}|{}".format(booking.localizator, booking.booking_code)
                    guest = Guest.objects.filter(ext_id=code, project_id=pau.project_uuid, deleted=0).first()
                    if guest == None:
                        guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=code, project_id=pau.project_uuid)
                        guest.name = booking.client.name
                        guest.surname = booking.client.surname
                        #guest.language = booking.client.languaje
                        guest.mobile = booking.client.phone
                        guest.email = booking.client.email
                        guest.check_in = checkin
                        guest.check_out = get_date(booking.end_date, booking.end_time, start_date)
                        guest.room = booking.accommodation_code
                        guest.save()
                        err = guest.add_all_key_code(code[-4:])
                        av.send_pwa_link(guest.ext_id, guest.pwa_link)

        #return HttpResponse(booking_list)
        return render(request, 'avantio/booking-list.html', {'booking_list': booking_list, "error": err})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})

@group_required("admins", "projects")
def avantio_get_booking_notif(request, project_uuid):
    try:
        pau = ProjectAvantioUser.objects.filter(project_uuid=project_uuid).first()
        booking_list = ""
        if pau != None:
            start_date, end_date = get_dates_range(pau)
            av = ShAvantio(pau.username, pau.password)
            booking_list = av.get_booking_notifications()
            for booking in booking_list:
                b = av.get_booking(booking.booking_code, booking.localizator)
                if b != None:
                    checkin = get_date(b.start_date, b.start_time, start_date)
                    if checkin >= start_date and checkin <= end_date:
                        code = "{}|{}".format(b.localizator, b.booking_code)
                        guest = Guest.objects.filter(ext_id=code, project_id=pau.project_uuid, deleted=0).first()
                        if guest == None:
                            guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=code, project_id=pau.project_uuid)

                        guest.name = b.client.name
                        guest.surname = b.client.surname
                        guest.mobile = b.client.phone
                        guest.email = b.client.email
                        guest.check_in = checkin
                        guest.check_out = get_date(b.end_date, b.end_time, start_date)
                        guest.room = b.accommodation_code
                        guest.save()

                        #if b.start_date != "" and b.start_time != "":
                        #    guest.check_in = datetime.strptime("{} {}".format(b.start_date, b.start_time), "%Y-%m-%d %H:%M")
                        #if b.end_date != "" and b.end_time != "":
                        #    guest.check_out = datetime.strptime("{} {}".format(b.end_date, b.end_time), "%Y-%m-%d %H:%M")
                        #guest.add_all_key_code(code[-4:])
                        #av.send_pwa_link(guest.ext_id, guest.pwa_link)
        return render(request, 'avantio/booking-notif.html', {'booking_list': booking_list})
    except Exception as e:
        print(e)
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


@group_required("admins")
def avantio_send_link(request, project_uuid, guest_uuid):
    try:
        resp = "---"
        pau = ProjectAvantioUser.objects.filter(project_uuid=project_uuid).first()
        if pau != None:
            guest = get_or_none(Guest, guest_uuid, "UUID")
            if guest != None:
                av = ShAvantio(pau.username, pau.password)
                resp = av.send_pwa_link(guest.ext_id, guest.pwa_link)
        return HttpResponse(resp)
    except Exception as e:
        return render(request, 'error_exception.html', {'exc':show_exc(e)})


