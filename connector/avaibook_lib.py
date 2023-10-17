from django.conf import settings
from datetime import datetime
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
    WEBHOOK_TOKEN = settings.AVAIBOOK_TOKEN
except:
    API_URL = "https://api.avaibook.biz/api/partner/"
    WEBHOOK_TOKEN = "SHLBM!CRspnXdsjy4xWt15l6=ngX4Dv6ujUw/S5XCVkPIXrM9WRNawn0zMg4S5GO"

BOOKINGS_URL = "booking/bookings"
ACCOMMODATIONS_URL = "accommodations"
SEND_LINK_URL = "booking/checkin/register-access-data"

def get_param(dic, key):
    return dic[key] if key in dic else ""

class AvaibookAPIError(Exception):
    def __init__(self, menssage='Invalid Parameter'):
        self.menssage=menssage

    def __str__(self):
        return 'Error: {}'.format(self.menssage)

class Avaibook():
    def __init__(self, uuid, token):
        self.token = token
        self.uuid = uuid
    
    def __send_request__(self, _url_request):
        try:
            #_headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Token': '43bedb65e2fa3a57dd19650c7f67a1cb648644f8'}
            _headers = {}
            _headers['Accept'] = 'application/json'
            _headers['Authorization'] = 'Basic {}'.format(self.uuid)
            _headers['Token'] = '{}'.format(self.token)
            _response = requests.get(_url_request, headers=_headers)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise AvaibookAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise AvaibookAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise AvaibookAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise AvaibookAPIError(menssage=err)

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
            raise AvaibookAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise AvaibookAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise AvaibookAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise AvaibookAPIError(menssage=err)

    def get_bookings(self):
        try:
            _url_request = "{}{}".format(API_URL, BOOKINGS_URL)
            return self.__send_request__(_url_request).json()["items"]
        except Exception as err:
            raise AvaibookAPIError(menssage=err)

    def get_accommodations(self):
        try:
            _url_request = "{}{}".format(API_URL, ACCOMMODATIONS_URL)
            return self.__send_request__(_url_request).json()["items"]
        except Exception as err:
            raise AvaibookAPIError(menssage=err)

    def send_pwa_link(self, booking_id, code, link):
        try:
            _url_request = "{}{}".format(API_URL, SEND_LINK_URL)
            json = {"booking_id": booking_id, "access_code": code, "access_link": link}
            return self.__send_post_request__(_url_request, json)
        except Exception as err:
            raise AvaibookAPIError(menssage=err)

class AvaibookBooking():
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

class AvaibookAccommodationLocation():
    def __init__(self, dic):
        self.address = get_param(dic, "address")
        self.zip_code = get_param(dic, "zip_code")
        self.city = get_param(dic, "city")
        self.region = get_param(dic, "region")
        self.country = get_param(dic, "country")
        self.area = get_param(dic, "area")
        self.longitude = get_param(dic, "longitude")
        self.latitude = get_param(dic, "latitude")

class AvaibookAccommodationUnit():
    def __init__(self, dic):
        self.id = get_param(dic, "id")
        self.name = dic["name"] if "name" in dic else {}

class AvaibookAccommodation():
    def __init__(self, dic, location, units):
        self.id = get_param(dic, "id")
        self.name = get_param(dic, "name")
        self.rental_type = get_param(dic, "rental_type")
        self.location = location
        self.units = units
 
'''
    FUNCTIONS
'''
def get_date(date, time):
    if time != None:
        return datetime.strptime("{} {}".format(date, time), "%Y-%m-%d %H:%M:%S")
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

    if room_ex:
        b_id = booking.webhook_id if booking.webhook_id != "" else booking.id
        guest = Guest.objects.filter(ext_id=b_id, project_id=pau.project_uuid, deleted=0).first()
        #guest = Guest.objects.filter(ext_id=booking.id, project_id=pau.project_uuid, deleted=0).first()
        if booking.action != "CANCELLATION":
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

            return guest
        else:
            if guest != None:
                guest.delete()
    return None

def get_booking_list(pau):
    #TOKEN = "43bedb65e2fa3a57dd19650c7f67a1cb648644f8"
    #UUID = "MyFoRlQ5YmZFNHZqSDFRR2JGYnFZUE0zYk5rUSo2VXo6JGFyZ29uMmlkJHY9MTkkbT02NTUzNix0PTQscD0xJFFDbEdhVVVQdXY5UmUrZEV0eklyS0EkSjc4UTk2OER0M2dZdno2M1JCZFk4dENCNHZaRm0zZWljRlMyeXlmaUlJVQ"
    #av = Avaibook(UUID, TOKEN)

    av = Avaibook(pau.uuid, pau.token)
    result = av.get_bookings()
    #print(result)
    booking_list = []
    for item in result:
        node = AvaibookBooking(item)
        booking_list.append(node)
        create_booking(pau, node, av)
    return booking_list

def create_accommodation(pau, acc):
    room = Room.objects.filter(project_uuid=pau.project_uuid, number=acc.id).first()
    if room != None:
        return room

    room =  Room.objects.create(project_uuid=pau.project_uuid, number=acc.id)
    room.alias = acc.name["es"]
    room.uuid = new_ui_slug(Room)
    #room.order = 
    room.save()
    #return room

def get_accommodation_list(pau):
    av = Avaibook(pau.uuid, pau.token)
    result = av.get_accommodations()
    item_list = []
    for item in result:
        unit_list = []
        for u in item["units"]:
            unit = AvaibookAccommodationUnit(u)
            unit_list.append(unit)
            create_accommodation(pau, unit)
        loc = AvaibookAccommodationLocation(item["location"]) if "location" in item else {}
        node = AvaibookAccommodation(item, loc, unit_list)
        item_list.append(node)
    return item_list

def create_booking_from_webhook(pau, booking):
    av = Avaibook(pau.uuid, pau.token)
    node = AvaibookBooking(booking)
    guest = create_booking(pau, node, av)
    #if guest != None:
    #    send_link(pau, guest)

def send_link(pau, guest):
    resp = "---"
    av = Avaibook(pau.uuid, pau.token)
    resp = av.send_pwa_link(guest.ext_id, "", guest.pwa_link)
    return resp

