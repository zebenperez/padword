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
    API_URL = settings.AVAIBOOK_API_URL
except:
    API_URL = "https://developer.siteminder.com"

BOOKINGS_URL = "reservations"

def get_param(dic, key):
    return dic[key] if key in dic else ""

class RoomRaccoomAPIError(Exception):
    def __init__(self, menssage='Invalid Parameter'):
        self.menssage=menssage

    def __str__(self):
        return 'Error: {}'.format(self.menssage)

class RoomRaccoom():
    def __init__(self, uuid, token):
        self.token = token
        self.uuid = uuid
    
    def __send_request__(self, _url_request, _params=""):
        try:
            _headers = {}
            _headers['Accept'] = 'application/json'
            _headers['x-sm-api-id'] = ''
            _headers['x-sm-api-key'] = ''
            #_headers['Authorization'] = 'Basic {}'.format(self.uuid)
            #_headers['Token'] = '{}'.format(self.token)
            if _params != "":
                _response = requests.get(_url_request, headers=_headers, params=_params)
            else:
                _response = requests.get(_url_request, headers=_headers)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise RoomRaccoomAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise RoomRaccoomAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise RoomRaccoomAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise RoomRaccoomAPIError(menssage=err)

    def __send_post_request__(self, _url_request, _json):
        try:
            #_headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Token': '43bedb65e2fa3a57dd19650c7f67a1cb648644f8'}
            _headers = {}
            _headers['Accept'] = 'application/json'
            _headers['Authorization'] = 'Basic {}'.format(self.uuid)
            _headers['Token'] = '{}'.format(self.token)
            _response = requests.post(_url_request, headers=_headers, json=_json)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise RoomRaccoomAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise RoomRaccoomAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise RoomRaccoomAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise RoomRaccoomAPIError(menssage=err)

    def get_bookings(self):
        try:
            _url_request = "{}{}".format(API_URL, BOOKINGS_URL)
            params = {
                "dateType": "checkIn",
                "fromDate": "2025-07-01",
                "toDate": "2025-07-30"
            }
            dic = self.__send_request__(_url_request, params).json()
            print(dic)
            return dic
        except Exception as err:
            raise RoomRaccoomAPIError(menssage=err)

#    def get_accommodations(self):
#        try:
#            _url_request = "{}{}".format(API_URL, ACCOMMODATIONS_URL)
#            params = {"page": 1, "limit": 100}
#            dic = self.__send_request__(_url_request, params).json()
#            items = dic["items"]
#            for i in range(2, dic["paginator"]["total_pages"]+1):
#                params = {"page": i, "limit": 100}
#                dic = self.__send_request__(_url_request, params).json()
#                items += dic["items"]
#            return items
#            #return self.__send_request__(_url_request, params).json()["items"]
#        except Exception as err:
#            raise RoomRaccoomAPIError(menssage=err)
#
#    def send_pwa_link(self, booking_id, code, link):
#        try:
#            _url_request = "{}{}".format(API_URL, SEND_LINK_URL)
#            json = {"booking_id": booking_id, "access_code": code, "access_link": link}
#            return self.__send_post_request__(_url_request, json)
#        except Exception as err:
#            raise RoomRaccoomAPIError(menssage=err)

class RoomRaccoomBooking():
    def __init__(self, dic):
        self.id = get_param(dic, "id")
        self.webhook_id = get_param(dic, "internal_booking_id")
        self.status = get_param(dic, "status")
        self.accommodation_id = get_param(dic, "accommodation_id")
        self.unit_id = get_param(dic, "unit_id")
        self.check_in_date = get_param(dic, "check_in_date")
        self.check_out_date = get_param(dic, "check_out_date")
        self.check_in_time = get_param(dic, "check_in_time")
        self.check_out_time = get_param(dic, "check_out_time")
        self.night_of_stay = get_param(dic, "night_of_stay")
        self.created_at = get_param(dic, "created_at")
        self.price = get_param(dic, "price")
        self.number_of_guests = get_param(dic, "number_of_guests")
        self.default_invite_email = get_param(dic, "default_invite_email")
        self.default_leader_full_name = get_param(dic, "default_leader_full_name")
        self.default_leader_phone = get_param(dic, "default_leader_phone")
        self.source = get_param(dic, "source")
        self.partner_name = get_param(dic, "partner_name")
        self.action = get_param(dic, "action")
        self.created = False

#class RoomRaccoomAccommodationLocation():
#    def __init__(self, dic):
#        self.address = get_param(dic, "address")
#        self.zip_code = get_param(dic, "zip_code")
#        self.city = get_param(dic, "city")
#        self.region = get_param(dic, "region")
#        self.country = get_param(dic, "country")
#        self.area = get_param(dic, "area")
#        self.longitude = get_param(dic, "longitude")
#        self.latitude = get_param(dic, "latitude")
#
#class RoomRaccoomAccommodationUnit():
#    def __init__(self, dic):
#        self.id = get_param(dic, "id")
#        self.name = dic["name"] if "name" in dic else {}
#
#class RoomRaccoomAccommodation():
#    def __init__(self, dic, location, units):
#        self.id = get_param(dic, "id")
#        self.name = get_param(dic, "name")
#        self.rental_type = get_param(dic, "rental_type")
#        self.location = location
#        self.units = units
 
'''
    FUNCTIONS
'''
def get_date(date, time):
    if time != None:
        return datetime.strptime("{} {}".format(date, time), "%Y-%m-%d %H:%M")
    else:
        return datetime.strptime("{} 13:00:00".format(date), "%Y-%m-%d %H:%M:%S")

def room_exist(project_uuid, room):
    count = Room.objects.filter(project_uuid=project_uuid, number=room).count()
    return (count > 0)

def create_booking(pau, booking, av):
    checkin = get_date(booking.check_in_date, booking.check_in_time)
    checkout = get_date(booking.check_out_date, booking.check_out_time)
    room = booking.unit_id
    room_ex = room_exist(pau.project_uuid, room)
    yesterday = datetime.today().replace(hour=23, minute=59, second=59) + timedelta(days=-1)
    err = ""

    if room_ex and checkout > yesterday:
        b_id = booking.webhook_id if booking.webhook_id != "" else booking.id
        guest = Guest.objects.filter(ext_id=b_id, project_id=pau.project_uuid, deleted=0).first()
        #guest = Guest.objects.filter(ext_id=booking.id, project_id=pau.project_uuid, deleted=0).first()
        #if booking.action != "CANCELLATION":
        if guest == None:
            guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=b_id, project_id=pau.project_uuid)
            booking.created = True
        
        guest.name = booking.default_leader_full_name
        guest.mobile = booking.default_leader_phone
        guest.email = booking.default_invite_email
        guest.check_in = checkin
        guest.check_out = checkout
        guest.room = room
        guest.save()

        if booking.created:
            #lock_code = guest.mobile[-4:]
            lock_code = ''.join([random.choice(string.digits) for i in range(4)])
            err = guest.add_all_key_code(lock_code)
            av.send_pwa_link(guest.ext_id, lock_code, guest.pwa_link)

        return guest, err
        #else:
        #    if guest != None:
        #        guest.delete()
    return None, err

#def delete_booking(pau, booking):
#    b_id = booking.webhook_id if booking.webhook_id != "" else booking.id
#    guest = Guest.objects.filter(ext_id=b_id, project_id=pau.project_uuid, deleted=0).first()
#    if guest != None:
#        guest.delete()
#    return None

def get_booking_list(pau):
    av = RoomRaccoom(pau.uuid, pau.token)
    result = av.get_bookings()
    #print(result)
    booking_list = []
    for item in result:
        node = RoomRaccoomBooking(item)
        booking_list.append(node)
        #create_booking(pau, node, av)
        if node.status == "CONFIRMED":
            guest, err = create_booking(pau, node, av)
        elif node.status == "CANCELLED":
            delete_booking(pau, node)
    return booking_list

#def create_accommodation(pau, acc):
#    room = Room.objects.filter(project_uuid=pau.project_uuid, number=acc.id).first()
#    if room != None:
#        return room
#
#    room =  Room.objects.create(project_uuid=pau.project_uuid, number=acc.id)
#    room.alias = acc.name["es"]
#    room.uuid = new_ui_slug(Room)
#    #room.order = 
#    room.save()
#    #return room
#
#def get_accommodation_list(pau):
#    av = RoomRaccoom(pau.uuid, pau.token)
#    result = av.get_accommodations()
#    item_list = []
#    for item in result:
#        unit_list = []
#        for u in item["units"]:
#            unit = RoomRaccoomAccommodationUnit(u)
#            unit_list.append(unit)
#            create_accommodation(pau, unit)
#        loc = RoomRaccoomAccommodationLocation(item["location"]) if "location" in item else {}
#        node = RoomRaccoomAccommodation(item, loc, unit_list)
#        item_list.append(node)
#    return item_list
#
#def manage_booking_from_webhook(pau, booking):
#    av = RoomRaccoom(pau.uuid, pau.token)
#    node = RoomRaccoomBooking(booking)
#    err = ""
#    if node.action == "CANCELLATION":
#        delete_booking(pau, node)
#    else:
#        guest, err = create_booking(pau, node, av)
#    return err
#    #if guest != None:
#    #    send_link(pau, guest)
#
#def send_link(pau, guest):
#    resp = "---"
#    av = RoomRaccoom(pau.uuid, pau.token)
#    resp = av.send_pwa_link(guest.ext_id, "", guest.pwa_link)
#    return resp

