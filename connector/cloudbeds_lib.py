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
    API_URL = "https://hotels.cloudbeds.com/api/v1.2/"

BOOKINGS_URL = "getReservations"
ROOMS_URL = "getRooms"
GUEST_URL = "getGuest"
CONFIRM_STATE = "confirmed"

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
            _response = requests.post(_url_request, headers=_headers, json=_json)
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


'''
    FUNCTIONS
'''
def get_ext_id(booking, room):
    return "{}_{}".format(booking.id, room.id)

def get_date(date):
    return datetime.strptime("{}".format(date), "%Y-%m-%d")
    #return datetime.strptime("{}".format(date), "%Y-%m-%dT%H:%M:%SZ")

def room_exist(project_uuid, room):
    count = Room.objects.filter(project_uuid=project_uuid, number=room).count()
    return (count > 0)

def create_booking(pmu, room, booking, bguest, av):
    checkin = get_date(room.check_in)
    checkout = get_date(room.check_out)
    #print(checkin)
    #print(checkout)
    r = room.id if room != None else "-1"
    room_ex = room_exist(pmu.project_uuid, r)
    err = ""

    if room_ex:
        ext_id = get_ext_id(booking, room)
        guest = Guest.objects.filter(ext_id=ext_id, project_id=pmu.project_uuid, deleted=0).first()
        if guest == None:
            guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=ext_id, project_id=pmu.project_uuid)
            booking.created = True
        
        #print(bguest)
        #print(bguest.first_name)
        guest.name = bguest.first_name
        guest.surname = bguest.last_name
        guest.mobile = bguest.cell_phone
        guest.email = bguest.email
        
        guest.check_in = checkin
        guest.check_out = checkout
        guest.room = r
        guest.save()

        #if booking.created:
            #lock_code = guest.mobile[-4:]
            #lock_code = ''.join([random.choice(string.digits) for i in range(4)])
            #lock_code = booking.number
            #err = guest.add_all_key_code(lock_code)
            #av.send_pwa_link(guest.ext_id, lock_code, guest.pwa_link)
#
#        return guest, err
#        #else:
        #    if guest != None:
        #        guest.delete()
    return None, err

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


#def cancel_booking_list(pmu):
#    av = Cloudbeds(pmu.client_token, pmu.access_token)
#    result = av.get_bookings(CANCELED_STATE)
#    #print(result)
#    booking_list = []
#    i = 0
#    for item in result:
#        i += 1
#        node = CloudbedsBooking(item)
#        booking_list.append(node)
#        delete_booking(pmu, node)
#    return booking_list
#
