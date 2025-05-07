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
    API_URL = settings.MEWS_API_URL
except:
    API_URL = "https://api.mews.com/api/connector/v1/"
    #API_URL = "https://api.mews-demo.com/api/connector/v1/"

BOOKINGS_URL = "reservations/getAll/2023-06-06"
CUSTOMERS_URL = "customers/getAll"
RESOURCES_URL = "resources/getAll"
CONFIRM_STATE = "Confirmed"
CANCELED_STATE = "Canceled"
#BOOKINGS_URL = "configuration/get"
#ACCOMMODATIONS_URL = "accommodations"
#SEND_LINK_URL = "booking/checkin/register-access-data"

def get_param(dic, key):
    return dic[key] if key in dic else ""

class MewsAPIError(Exception):
    def __init__(self, menssage='Invalid Parameter'):
        self.menssage=menssage

    def __str__(self):
        return 'Error: {}'.format(self.menssage)

class Mews():
    def __init__(self, client_token, access_token):
        self.client_token = client_token
        self.access_token = access_token
        self.ini_date = datetime.now().strftime("%Y-%m-%dT00:00:00Z")
        self.end_date = datetime.now().strftime("%Y-%m-%dT23:59:59Z")
        #self.ini_date = "2024-03-14T00:00:00Z"
        #self.end_date = "2024-03-14T23:59:59Z"
    
    def __send_request__(self, _url_request, _params=""):
        try:
            _headers = {}
            _headers['Accept'] = 'application/json'
            #_headers['Authorization'] = 'Basic {}'.format(self.uuid)
            #_headers['Token'] = '{}'.format(self.token)
            if _params != "":
                _response = requests.get(_url_request, headers=_headers, params=_params)
            else:
                _response = requests.get(_url_request, headers=_headers)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise MewsAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise MewsAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise MewsAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise MewsAPIError(menssage=err)

    def __send_post_request__(self, _url_request, _json):
        try:
            _headers = {}
            _headers['Accept'] = 'application/json'
            #_headers['Authorization'] = 'Basic {}'.format(self.uuid)
            #_headers['Token'] = '{}'.format(self.token)
            _response = requests.post(_url_request, headers=_headers, json=_json)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise MewsAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise MewsAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise MewsAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise MewsAPIError(menssage=err)

    def get_bookings(self, state=CONFIRM_STATE):
        try:
            _url_request = "{}{}".format(API_URL, BOOKINGS_URL)
            params = {
                    "ClientToken": "{}".format(self.client_token),
                    "AccessToken": "{}".format(self.access_token),
                    "Client": "Padword",
                    "Limitation": {
                        #"Cursor": "819e3435-7d5e-441f-bc68-76d89c69b8f5",
                        "Count": 100
                    },
                    "CreatedUtc": {
                        "StartUtc": self.ini_date,
                        "EndUtc": self.end_date
                    },
                    "States": [state]
                    #"AccountIds": [
                    #    "1b768e9c-ffdd-485c-95e8-3c96d3f9c4cc"
                    #],
                    #"ScheduleStartUtc": {
                    #    "StartUtc": "2024-03-12T00:00:00Z",
                    #    "EndUtc": "2024-03-15T00:00:00Z"
                    #},
                    #"UpdatedUtc": {
                    #    "StartUtc": "2023-04-01T00:00:00Z",
                    #    "EndUtc": "2023-05-05T00:00:00Z"
                    #},
                    #"States": ["Confirmed", "Started"]
            }
            dic = self.__send_post_request__(_url_request, params).json()
            items = dic["Reservations"]
            return items
        except Exception as err:
            raise MewsAPIError(menssage=err)

    def get_customer(self, customer_id):
        try:
            _url_request = "{}{}".format(API_URL, CUSTOMERS_URL)
            params = {
                    "ClientToken": "{}".format(self.client_token),
                    "AccessToken": "{}".format(self.access_token),
                    "Client": "Padword",
                    "CustomerIds": [customer_id]
            }
            dic = self.__send_post_request__(_url_request, params).json()
            items = dic["Customers"]
            return items
        except Exception as err:
            raise MewsAPIError(menssage=err)

    def get_resource(self, resource_id):
        try:
            _url_request = "{}{}".format(API_URL, RESOURCES_URL)
            params = {
                    "ClientToken": "{}".format(self.client_token),
                    "AccessToken": "{}".format(self.access_token),
                    "Client": "Padword",
                    "ResourceIds": [resource_id]
            }
            dic = self.__send_post_request__(_url_request, params).json()
            items = dic["Resources"]
            return items
        except Exception as err:
            raise MewsAPIError(menssage=err)


class MewsBooking():
    def __init__(self, dic):
        self.id = get_param(dic, "Id")
        self.service_id = get_param(dic, "ServiceId")
        self.account_id = get_param(dic, "AccountId")
        self.booker_id = get_param(dic, "BookerId")
        self.start = get_param(dic, "StartUtc")
        self.end = get_param(dic, "EndUtc")
        self.created = get_param(dic, "CreatedUtc")
        self.updated = get_param(dic, "UpdatedUtc")
        self.number = get_param(dic, "Number")
        self.state = get_param(dic, "State")
        self.resource_id = get_param(dic, "AssignedResourceId")
        self.customer = None
        self.room = None
        self.created = False

class MewsCustomer():
    def __init__(self, dic):
        self.id = get_param(dic, "Id")
        self.name = "{} {}".format(get_param(dic, "FirstName"), get_param(dic, "LastName"))
        self.phone = get_param(dic, "Phone")
        self.email = get_param(dic, "Email")

class MewsResource():
    def __init__(self, dic):
        self.id = get_param(dic, "Id")
        self.number = get_param(dic, "Name")

'''
    FUNCTIONS
'''
def get_ext_id(booking):
    return "{}__{}".format(booking.id, booking.number)

def get_date(date):
    return datetime.strptime("{}".format(date), "%Y-%m-%dT%H:%M:%SZ")

def room_exist(project_uuid, room):
    count = Room.objects.filter(project_uuid=project_uuid, number=room).count()
    return (count > 0)

def create_booking(pmu, booking, av):
    checkin = get_date(booking.start)
    checkout = get_date(booking.end)
    #print(checkin)
    #print(checkout)
    room = booking.room.number if booking.room != None else "-1"
    room_ex = room_exist(pmu.project_uuid, room)
    err = ""

    if room_ex and "Z" in room:
        ext_id = get_ext_id(booking)
        guest = Guest.objects.filter(ext_id=ext_id, project_id=pmu.project_uuid, deleted=0).first()
        if guest == None:
            guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=ext_id, project_id=pmu.project_uuid)
            booking.created = True
        
        if booking.customer != None:
            guest.name = booking.customer.name
            guest.mobile = booking.customer.phone if booking.customer.phone != None else ""
            guest.email = booking.customer.email if booking.customer.email != None else ""
        
        guest.check_in = checkin
        guest.check_out = checkout
        guest.room = room
        guest.save()

        if booking.created:
            #lock_code = guest.mobile[-4:]
            #lock_code = ''.join([random.choice(string.digits) for i in range(4)])
            lock_code = booking.number
            err = guest.add_all_key_code(lock_code)
            #av.send_pwa_link(guest.ext_id, lock_code, guest.pwa_link)
#
#        return guest, err
#        #else:
        #    if guest != None:
        #        guest.delete()
    return None, err

def delete_booking(pwu, booking):
    ext_id = get_ext_id(booking)
    guest = Guest.objects.filter(ext_id=ext_id, project_id=pwu.project_uuid, deleted=0).first()
    if guest != None:
        guest.delete()

def get_booking_list(pmu):
    av = Mews(pmu.client_token, pmu.access_token)
    result = av.get_bookings()
    #print(result)
    booking_list = []
    i = 0
    for item in result:
        i += 1
        node = MewsBooking(item)
        booking_list.append(node)

        customers = av.get_customer(node.account_id)
        for customer in customers:
            node_c = MewsCustomer(customer)
            node.customer = node_c
            break

        if (node.resource_id != None):
            rooms = av.get_resource(node.resource_id)
            for room in rooms:
                node_r = MewsResource(room)
                node.room = node_r
                break

        create_booking(pmu, node, av)
        #if node.status == "CONFIRMED":
        #    guest, err = create_booking(pau, node, av)
        #elif node.status == "CANCELLED":
        #    delete_booking(pau, node)
    #print("Total: {}".format(i))
    return booking_list

def cancel_booking_list(pmu):
    av = Mews(pmu.client_token, pmu.access_token)
    result = av.get_bookings(CANCELED_STATE)
    #print(result)
    booking_list = []
    i = 0
    for item in result:
        i += 1
        node = MewsBooking(item)
        booking_list.append(node)
        delete_booking(pmu, node)
    return booking_list

