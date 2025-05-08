from django.conf import settings
from datetime import datetime, timedelta
from web.models import Room
from guest.models import Guest
from padword.commons import new_ui_slug

import requests
import hashlib
import urllib
import json
import random
import string

try:
    API_URL = settings.CLOUDBEDS_API_URL
except:
    API_URL = "https://api.cloudbeds.com/api/v1.2/"

BOOKINGS_URL = "getReservations"
BOOKING_URL = "getReservation"
ROOMS_URL = "getRooms"
GUEST_URL = "getGuest"
BOOKING_PUT_URL = "putReservation"
WEBHOOK_URL = "postWebhook"
CONFIRM_STATE = "confirmed"
END_POINT_URL = "{}/connector/cloudbeds/webhook/".format(settings.MAIN_URL)

def get_param(dic, key):
    return dic[key] if key in dic else ""

class CloudbedsAPIError(Exception):
    def __init__(self, menssage='Invalid Parameter'):
        self.menssage=menssage

    def __str__(self):
        return 'Error: {}'.format(self.menssage)

class Cloudbeds():
    def __init__(self, token):
        self.token = token
    
    def __send_request__(self, _url_request, _params=""):
        try:
            _headers = {}
            _headers['Accept'] = 'application/json'
            _headers['x-api-key'] = '{}'.format(self.token)
            if _params != "":
                _response = requests.get(_url_request, headers=_headers, params=_params)
            else:
                _response = requests.get(_url_request, headers=_headers)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise CloudbedsAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise CloudbedsAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise CloudbedsAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise CloudbedsAPIError(menssage=err)

    def __send_post_request__(self, _url_request, _json):
        try:
            _headers = {}
            _headers['Accept'] = 'application/json'
            _headers['x-api-key'] = '{}'.format(self.token)
            _response = requests.post(_url_request, headers=_headers, data=_json)
            #_response = requests.post(_url_request, headers=_headers, json=_json)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise CloudbedsAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise CloudbedsAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise CloudbedsAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise CloudbedsAPIError(menssage=err)

    def __send_put_request__(self, _url_request, _json):
        try:
            _headers = {}
            #_headers['Accept'] = 'application/json'
            #_headers['x-api-key'] = '{}'.format(self.token)
            _headers['Authorization'] = 'Bearer {}'.format(self.token)
            _headers['Content-Type'] = 'application/x-www-form-urlencoded'
            _response = requests.put(_url_request, headers=_headers, data=_json)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise CloudbedsAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise CloudbedsAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise CloudbedsAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise CloudbedsAPIError(menssage=err)


    def get_bookings(self, status=CONFIRM_STATE):
        try:
            _url_request = "{}{}".format(API_URL, BOOKINGS_URL)
            params = {
                "includeAllRooms": "true",
                "status": "confirmed"
            }
            dic = self.__send_request__(_url_request, params).json()
            items = dic["data"]
            return items
        except Exception as err:
            raise CloudbedsAPIError(menssage=err)

    def get_booking(self, booking_id):
        try:
            _url_request = "{}{}".format(API_URL, BOOKING_URL)
            dic = self.__send_request__(_url_request, {"reservationID":booking_id}).json()
            items = dic["data"]
            return items
        except Exception as err:
            raise CloudbedsAPIError(menssage=err)

    def get_rooms(self):
        try:
            _url_request = "{}{}".format(API_URL, ROOMS_URL)
            dic = self.__send_request__(_url_request, {}).json()
            items = dic["data"][0]["rooms"]
            return items
        except Exception as err:
            raise CloudbedsAPIError(menssage=err)

    def get_guest(self, guest_id):
        try:
            _url_request = "{}{}".format(API_URL, GUEST_URL)
            dic = self.__send_request__(_url_request, {"guestID":guest_id}).json()
            items = dic["data"]
            return items
        except Exception as err:
            raise CloudbedsAPIError(menssage=err)

    def set_booking_code(self, booking_id, param, code):
        try:
            _url_request = "{}{}".format(API_URL, BOOKING_PUT_URL)
            params = {
                'reservationID': booking_id,
                'customFields[0][customFieldName]': param,
                'customFields[0][customFieldValue]': code
            }
            dic = self.__send_put_request__(_url_request, params).json()
            #dic = self.__send_put_request__(_url_request, json.dumps(params)).json()
            #print(dic)
            items = dic["data"]
            return items
        except Exception as err:
            raise CloudbedsAPIError(menssage=err)

    def get_webhook(self, property_id):
        try:
            _url_request = "{}{}".format(API_URL, WEBHOOK_URL)
            params = { "propertyID": property_id }
            dic = self.__send_request__(_url_request, params).json()
            return dic
        except Exception as err:
            raise CloudbedsAPIError(menssage=err)

    def set_webhook(self, obj, action, property_id):
        try:
            _url_request = "{}{}".format(API_URL, WEBHOOK_URL)
            params = {
                "endpointUrl": END_POINT_URL,
                "object": obj,
                "action": action,
                "propertyID": property_id
            }
            dic = self.__send_post_request__(_url_request, params).json()
            return ""
        except Exception as err:
            raise CloudbedsAPIError(menssage=err)

#    def get_customer(self, customer_id):
#        try:
#            _url_request = "{}{}".format(API_URL, CUSTOMERS_URL)
#            params = {
#                    "ClientToken": "{}".format(self.client_token),
#                    "AccessToken": "{}".format(self.access_token),
#                    "Client": "Padword",
#                    "CustomerIds": [customer_id]
#            }
#            dic = self.__send_post_request__(_url_request, params).json()
#            items = dic["Customers"]
#            return items
#        except Exception as err:
#            raise CloudbedsAPIError(menssage=err)
#
#    def get_resource(self, resource_id):
#        try:
#            _url_request = "{}{}".format(API_URL, RESOURCES_URL)
#            params = {
#                    "ClientToken": "{}".format(self.client_token),
#                    "AccessToken": "{}".format(self.access_token),
#                    "Client": "Padword",
#                    "ResourceIds": [resource_id]
#            }
#            dic = self.__send_post_request__(_url_request, params).json()
#            items = dic["Resources"]
#            return items
#        except Exception as err:
#            raise CloudbedsAPIError(menssage=err)


class CloudbedsBooking():
    def __init__(self, dic):
        self.id = get_param(dic, "reservationID")
        self.property_id = get_param(dic, "propertyID")
        self.source_id = get_param(dic, "sourceID")
        self.source_name = get_param(dic, "sourceName")
        self.guest_id = get_param(dic, "guestID")
        self.guest_name = get_param(dic, "guestName")
        self.start = get_param(dic, "startDate")
        self.end = get_param(dic, "endDate")
        self.created = get_param(dic, "dateCreated")
        self.updated = get_param(dic, "dateModified")
        self.status = get_param(dic, "status")
        self.adults = get_param(dic, "adults")
        self.children = get_param(dic, "children")
        self.balance = get_param(dic, "balance")
        #self.customer = None
        self.rooms = []
        self.created = False

class CloudbedsBookingRoom():
    def __init__(self, dic):
        self.id = get_param(dic, "roomID")
        self.check_in = get_param(dic, "roomCheckIn")
        self.check_out = get_param(dic, "roomCheckOut")
        self.status = get_param(dic, "roomStatus")
        self.name = get_param(dic, "roomName")
        self.subreservation_id = get_param(dic, "subReservationID")
        self.type_id = get_param(dic, "roomTypeID")
        self.type_name = get_param(dic, "roomTypeName")
        self.guest_id = get_param(dic, "guestID")
        self.guest_name = get_param(dic, "guestName")
        self.adults = get_param(dic, "adults")
        self.children = get_param(dic, "children")

class CloudbedsGuest():
    def __init__(self, dic):
        self.id = get_param(dic, "guestID")
        self.first_name = get_param(dic, "firstName")
        self.last_name = get_param(dic, "lastName")
        self.email = get_param(dic, "email")
        self.phone = get_param(dic, "phone")
        self.cell_phone = get_param(dic, "cellPhone")
        self.country = get_param(dic, "country")

class CloudbedsGuest2():
    def __init__(self, dic):
        self.id = get_param(dic, "guestID")
        self.first_name = get_param(dic, "guestFirstName")
        self.last_name = get_param(dic, "guestLastName")
        self.email = get_param(dic, "guestEmail")
        self.phone = get_param(dic, "guestPhone")
        self.cell_phone = get_param(dic, "guestCellPhone")
        self.country = get_param(dic, "guestCountry")

class CloudbedsRoom():
    def __init__(self, dic):
        self.id = get_param(dic, "roomID")
        self.name = get_param(dic, "roomName")
        self.description = get_param(dic, "roomDescription")
        self.max_guests = get_param(dic, "maxGuests")
        self.is_private = get_param(dic, "isPrivate")
        self.is_virtual = get_param(dic, "isVirtual")
        self.room_blocked = get_param(dic, "roomBlocked")
        self.type_id = get_param(dic, "roomTypeID")
        self.type_name = get_param(dic, "roomTypeName")
        self.type_name_short = get_param(dic, "roomTypeNameShort")

class CloudbedsRoom2():
    def __init__(self, dic):
        self.id = get_param(dic, "roomID")
        self.name = get_param(dic, "roomName")
        self.type_name = get_param(dic, "roomTypeName")
        self.check_in = ""
        self.check_out = ""


'''
    FUNCTIONS
'''
def get_ext_id(booking, room):
    return "{}".format(booking.id)
    #return "{}_{}".format(booking.id, room.id)

def get_code(pcu, mobile=""):
    return mobile.rstrip()[-4:] if pcu.code_mobile and mobile != "" else ''.join([random.choice(string.digits) for i in range(4)]) 

def get_date(date, hour, minute):
    return datetime.strptime("{} {}:{}".format(date, hour, minute), "%Y-%m-%d %H:%M")
    #return datetime.strptime("{}".format(date), "%Y-%m-%dT%H:%M:%SZ")

def room_exist(project_uuid, room):
    count = Room.objects.filter(project_uuid=project_uuid, number=room).count()
    return (count > 0)

def send_lock_code(pcu, guest, booking_id):
    lock_code = get_code(pcu, guest.mobile)
    err = guest.add_all_key_code(lock_code)
    av = Cloudbeds(pcu.token)
    av.set_booking_code(booking_id, "lockCode", lock_code)
    av.set_booking_code(booking_id, "lockLink", guest.pwa_link)

def create_booking(pcu, room, booking, bguest, av):
    #checkin = get_date(room.check_in, pcu.ini_time.hour, pcu.ini_time.minute)
    #checkout = get_date(room.check_out, pcu.end_time.hour, pcu.end_time.minute)
    checkin = get_date(booking.start, pcu.ini_time.hour, pcu.ini_time.minute)
    checkout = get_date(booking.end, pcu.end_time.hour, pcu.end_time.minute)
    today = datetime.today()
    e_date = today + timedelta(pcu.days)
    #end_date = e_date.strftime("%Y-%m-%d") 
    #print(checkin)
    #print(checkout)
    r = room.id if room != None else "-1"
    room_ex = room_exist(pcu.project_uuid, r)
    err = ""
    msg = ""
    #msg += "\n Habitación: {} ({}) - {}".format(r, room_ex, booking.status)
    #msg += "\n Fechas: {} {} {}".format(checkin, e_date, today)

    if room_ex and booking.status == "confirmed" and checkin <= e_date and checkin >= today:
        #msg += "\n Entrando"
        ext_id = get_ext_id(booking, room)
        guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
        if guest == None:
            guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=ext_id, project_id=pcu.project_uuid)
            booking.created = True
        
        change_booking = True if guest.check_in != checkin or guest.check_out != checkout or guest.room != r else False
        #print(bguest)
        #print(bguest.first_name)
        guest.name = bguest.first_name
        guest.surname = bguest.last_name
        guest.mobile = bguest.cell_phone
        guest.email = bguest.email
        guest.language = bguest.country
        
        guest.check_in = checkin
        guest.check_out = checkout
        guest.room = r
        guest.save()
        msg += "\n Asignando: {} ({})".format(guest.room, guest.name)

        if booking.created:
            msg += "\n CREADA"
            lock_code = get_code(pcu, guest.mobile)
            #msg += "-- CODE: {} - mobile {} - code mobile{}".format(lock_code, guest.mobile, pcu.code_mobile)
            #print(lock_code)
            err = guest.add_all_key_code(lock_code)
            msg += "\n {}".format(err)
            av.set_booking_code(booking.id, "lockCode", lock_code)
            av.set_booking_code(booking.id, "lockLink", guest.pwa_link)
        elif change_booking:
            msg += "\n MODIFICADA"
            guest.change_room(r)

#        return guest, err
#        #else:
        #    if guest != None:
        #        guest.delete()
    return msg
    #return None, err

def create_room(pcu, room, index):
    r = Room.objects.filter(project_uuid=pcu.project_uuid, number=room.id).first()
    if r != None:
        return r

    r =  Room.objects.create(project_uuid=pcu.project_uuid, number=room.id)
    r.alias = room.name
    r.uuid = new_ui_slug(Room)
    r.order = index 
    r.save()

#def delete_booking(pwu, booking):
#    ext_id = get_ext_id(booking)
#    guest = Guest.objects.filter(ext_id=ext_id, project_id=pwu.project_uuid, deleted=0).first()
#    if guest != None:
#        guest.delete()

def get_booking_list(pcu):
    #get_or_create_booking(pcu, "1880682788524")
    av = Cloudbeds(pcu.token)
    result = av.get_bookings()
    #print(result)
    booking_list = []
    i = 0
    for item in result:
        #print(item)
        i += 1
        node = CloudbedsBooking(item)
        room_list = get_param(item, "rooms")
        for room in room_list:
            #print(room)
            room_node = CloudbedsBookingRoom(room)
            guest = av.get_guest(room_node.guest_id)
            guest_node = CloudbedsGuest(guest)
            create_booking(pcu, room_node, node, guest_node, av)
            node.rooms.append(room_node)
        booking_list.append(node)
    return booking_list

def get_room_list(pcu):
    av = Cloudbeds(pcu.token)
    result = av.get_rooms()
    #print(result)
    room_list = []
    i = 0
    for item in result:
        i += 1
        node = CloudbedsRoom(item)
        create_room(pcu, node, i)
        room_list.append(node)
    return room_list

def get_webhooks(pcu):
    av = Cloudbeds(pcu.token)
    result = av.get_webhook(pcu.property_id)
    if "data" in result:
        datas = []
        for r in result["data"]:
            datas.append(r)
            #datas[r["id"]] = r["event"]
    else: 
        datas = result
    return datas

def set_webhooks(pcu):
    av = Cloudbeds(pcu.token)
    #result = av.set_webhook("reservation", "created", pcu.property_id)
    result += av.set_webhook("reservation", "status_changed", pcu.property_id)
    result += av.set_webhook("reservation", "dates_changed", pcu.property_id)
    result += av.set_webhook("reservation", "accommodation_changed", pcu.property_id)
    result += av.set_webhook("reservation", "deleted", pcu.property_id)
#    result += av.set_webhook("guest", "created", pcu.property_id)
    #result += av.set_webhook("guest", "assigned", pcu.property_id)
#    result += av.set_webhook("guest", "accommodation_changed", pcu.property_id)
    return ""

def manage_webhook_actions(pcu, obj):
    msg = ""
    #if obj["event"] == "reservation/created":
        #reservation_create(pcu, obj)
    #    msg = "\n-- Creada la reserva {}".format(obj["reservationID"])
    #    msg += get_or_create_booking(pcu, obj["reservationID"])

    if obj["event"] == "reservation/status_changed":
        #reservation_status_change(pcu, obj)
        msg = "\n-- Modificado el estado de la reserva {}".format(obj["reservationID"])
        msg += get_or_create_booking(pcu, obj["reservationID"])

    if obj["event"] == "reservation/dates_changed":
        #reservation_dates_change(pcu, obj)
        msg = "\n-- Modificadas las fechas de la reserva {}".format(obj["reservationId"])
        msg += get_or_create_booking(pcu, obj["reservationId"])

    if obj["event"] == "reservation/accommodation_changed":
        #reservation_room_change(pcu, obj)
        msg = "\n-- Modificada la habitación de la reserva {}".format(obj["reservationId"])
        msg += get_or_create_booking(pcu, obj["reservationId"])

    if obj["event"] == "reservation/deleted":
        reservation_delete(pcu, obj)
        msg = "\n-- Eliminada la reserva {}".format(obj["reservationId"])

#    if obj["event"] == "guest/created":
#        guest_create(pcu, obj)
#        msg = "\n-- Creado el huésped {}".format(obj["guestId"])

    #if obj["event"] == "guest/assigned":
        #guest_assigned(pcu, obj)
    #    msg = "\n-- Asignado el huésped {} a la reserva {}".format(obj["guestId"], obj["reservationId"])
    #    msg += get_or_create_booking(pcu, obj["reservationId"])

#    if obj["event"] == "guest/accommodation_changed":
#        guest_room_change(pcu, obj)
#        msg = "\n-- Modificada la habitación del huésped {} en la reserva {}".format(obj["guestId"], obj["reservationId"])

    return msg

def get_or_create_booking(pcu, ext_id):
    msg = ""
    av = Cloudbeds(pcu.token)
    booking = av.get_booking(ext_id)
    #msg += "\n --1--"
    #msg += "\n {}".format(booking)
    node = CloudbedsBooking(booking)

    msg += "\n -- Estado: {}".format(node.status)
    if node.status == "canceled" or node.status == "check_out":
        #msg += "\n -- Cancelada."
        guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
        if guest != None:
            msg += "\n -- Borrando."
            guest.delete_soft()
    else:
        guest_list = get_param(booking, "guestList")
        for guest_id in guest_list:
            datas = guest_list[guest_id]
            #msg += "\n --2--"
            #msg += "\n {}".format(datas)
            #print(datas)
            guest_node = CloudbedsGuest2(datas)
            room_node = CloudbedsRoom2(datas)
            #msg += "\n --3--"
            msg_g = create_booking(pcu, room_node, node, guest_node, av)
            msg += "\n {}".format(msg_g)
            #msg += "\n --4--"
            #msg += "\n {} {}".format(guest.name, guest.room)
            break
    return msg

#def reservation_create(pcu, obj):
#    ext_id = obj["reservationID"]
#    checkin = get_date(obj["startDate"])
#    checkout = get_date(obj["endDate"])
#    
#    guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
#    if guest == None:
#        av = Cloudbeds(pcu.token)
#        booking = av.get_booking(ext_id)
#        b = CloudbedsBooking(booking)
#        if b.status == "confirmed": 
#            new_uuid = new_ui_slug(Guest, "UUID")
#            guest = Guest.objects.create(UUID=new_uuid,ext_id=ext_id,project_id=pcu.project_uuid,check_in=checkin,check_out=checkout)
#
#    return guest
#
#def reservation_status_change(pcu, obj):
#    ext_id = obj["reservationID"]
#    status = obj["status"]
#    status_list = ["in_progress", "confirmed", "not_confirmed", "canceled", "checked_in", "checked_out", "no_show"]
#
#    #in_progress se ignora
#    #not_confirmed se ignora
#    #check_in se ignora
#    #no_show se ignora
#
#    #confirmed si no está creada se crea
#    if status == "confirmed":
#        guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
#        if guest == None:
#            new_uuid = new_ui_slug(Guest, "UUID")
#            guest = Guest.objects.create(UUID=new_uuid,ext_id=ext_id,project_id=pcu.project_uuid,check_in=checkin,check_out=checkout)
#
#    #canceled hacer soft_remove
#    #check_out hacer soft_remove
#    if status == "canceled" or status == "check_out":
#        guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
#        if guest != None:
#            guest.delete_soft()
#
#    return ""
#
#def reservation_dates_change(pcu, obj):
#    ext_id = obj["reservationId"]
#    checkin = get_date(obj["startDate"])
#    checkout = get_date(obj["endDate"])
#    guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
#    if guest != None:
#        guest.check_in = checkin
#        guest.check_out = checkout
#        guest.save()
#    return ""
#
#def reservation_room_change(pcu, obj):
#    ext_id = obj["reservationId"]
#    room_id = obj["roomId"]
#    guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
#    if guest != None:
#        if room_exist(pcu.project_uuid, room_id):
#            guest.change_room(room_id)
#            send_lock_code(pcu, guest, ext_id)
#    return ""

def reservation_delete(pcu, obj):
    ext_id = obj["reservationId"]
    guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
    if guest != None:
        guest.delete_soft()
    return ""

#def guest_create(pcu, obj):
#    guest_id = obj["guestId"]
#    return ""

#def guest_assigned(pcu, obj):
#    guest_id = obj["guestId"]
#    ext_id = obj["reservationId"]
#    room_id = obj["roomId"]
#    guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
#    if guest != None:
#        av = Cloudbeds(pcu.token)
#        guest_json = av.get_guest(guest_id)
#        g = CloudbedsGuest(guest_json)
#        guest.name = g.first_name
#        guest.surname = g.last_name
#        guest.mobile = g.cell_phone
#        guest.email = g.email
#        guest.save()
#        if room_exist(pcu.project_uuid, room_id):
#            guest.change_room(room_id)
#            send_lock_code(pcu, guest, ext_id)
#    return ""
#
#def guest_room_change(pcu, obj):
#    guest_id = obj["guestId"]
#    ext_id = obj["reservationId"]
#    room_id = obj["roomId"]
#    guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
#    if guest != None:
#        if room_exist(pcu.project_uuid, room_id):
#            guest.change_room(room_id)
#    return ""

