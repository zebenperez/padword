from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext as _
from datetime import datetime, timedelta
from web.models import Room, Project
from guest.models import Guest, KeyCode
from padword.commons import new_ui_slug
from padword.email_lib import send_email

import requests
import hashlib
import urllib
import json
import random
import string
import os

try:
    API_URL = settings.MEWS_API_URL
    CLIENT_ID = settings.MEWS_CLIENT_ID
except:
    API_URL = "https://api.mews.com/api/connector/v1/"
    CLIENT_ID = "Padword"

BOOKINGS_URL = "reservations/getAll/2023-06-06"
CUSTOMERS_URL = "customers/getAll"
RESOURCES_URL = "resources/getAll"
CONFIRM_STATE = "Confirmed"
STARTED_STATE = "Started"
CANCELED_STATE = "Canceled"
INSPECTED_STATE = "Inspected"

def get_param(dic, key):
    return dic[key] if key in dic else ""

def write_log(result):
    f = open(os.path.join(settings.BASE_DIR, "mews.log"), "a", encoding='utf-8')
    f.write("{}\n".format(result))
    f.close()

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
    
    def __send_request__(self, _url_request, _params=""):
        try:
            _headers = {}
            _headers['Accept'] = 'application/json'
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

    def get_bookings(self, state=STARTED_STATE):
        try:
            _url_request = "{}{}".format(API_URL, BOOKINGS_URL)
            #print(_url_request)
            params = {
                    "ClientToken": "{}".format(self.client_token),
                    "AccessToken": "{}".format(self.access_token),
                    "Client": CLIENT_ID,
                    "Limitation": {
                        "Count": 1000
                    },
                    "CreatedUtc": {
                        "StartUtc": self.ini_date,
                        "EndUtc": self.end_date
                    },
                    "States": [state]
            }
            #print(params)
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

    def get_resources(self):
        try:
            _url_request = "{}{}".format(API_URL, RESOURCES_URL)
            params = {
                    "ClientToken": "{}".format(self.client_token),
                    "AccessToken": "{}".format(self.access_token),
                    "Client": "Padword",
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
        #self.start = get_param(dic, "StartUtc")
        #self.end = get_param(dic, "EndUtc")
        self.start = get_param(dic, "ActualStartUtc")
        if self.start is None:
            self.start = get_param(dic, "ScheduledStartUtc")
        self.end = get_param(dic, "ActualEndUtc")
        if self.end is None:
            self.end = get_param(dic, "ScheduledEndUtc")
        self.create_date = get_param(dic, "CreatedUtc")
        self.update_date = get_param(dic, "UpdatedUtc")
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
        self.language = get_param(dic, "LanguageCode")

class MewsResource():
    def __init__(self, dic):
        self.id = get_param(dic, "Id")
        self.number = get_param(dic, "Name")
        self.state = get_param(dic, "State")

'''
    FUNCTIONS
'''
def get_ext_id(booking):
    return "{}__{}".format(booking.id, booking.number)

def get_date(date):
    return datetime.strptime("{}".format(date), "%Y-%m-%dT%H:%M:%SZ")

def get_code(project):
    code = ""
    kc = 1
    while kc > 0:
        code = ''.join([random.choice(string.digits) for i in range(4)]) 
        kc = KeyCode.objects.filter(guest__project_id=project.uuid, code=code).count()
    return code

def room_exist(project_uuid, room):
    count = Room.objects.filter(project_uuid=project_uuid, number=room).count()
    return (count > 0)

def send_email_code(guest, code, pmu):
    from django.utils import translation

    try:
        subject = _("Códigos de acceso")
        body = ""
        with translation.override(guest.language.lower()):
            body = render_to_string("mews/email_template.html", {'guest': guest, 'project': guest.project, 'code': code, 'pmu': pmu})
        send_email(subject, "", settings.EMAIL_FROM_DEFAULT, [guest.email], body)
    except Exception as e:
        print(e)
    return body

def create_booking(pmu, booking, av):
    project = Project.objects.filter(uuid=pmu.project_uuid).first()
    checkin = project.local_date(get_date(booking.start))
    checkout = project.local_date(get_date(booking.end))
    #checkin = get_date(booking.start)
    #checkout = get_date(booking.end)
    room = booking.room.number if booking.room != None else "-1"
    room_inspected = True if booking.room != None and booking.room.state == INSPECTED_STATE else False
    room_ex = room_exist(pmu.project_uuid, room)
    err = ""

    write_log("---- CREANDO RESERVA MEWS")
    write_log(f"ID: {booking.id} - Número:{booking.number} - Checkin:{checkin} - Checkout:{checkout}")

    if room_ex and room_inspected: # Si el huésped tiene habitación asignada y está "Inspected"
        write_log("--Reserva con habitación 'inspeccionada'")
        ext_id = get_ext_id(booking)
        guest = Guest.objects.filter(ext_id=ext_id, project_id=pmu.project_uuid, deleted=0).first()
        if guest == None:
            write_log("--Reserva CREADA")
            guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=ext_id, project_id=pmu.project_uuid)
            booking.created = True
        
        if booking.customer != None:
            guest.name = booking.customer.name
            guest.mobile = booking.customer.phone if booking.customer.phone != None else ""
            guest.email = booking.customer.email if booking.customer.email != None else ""
            guest.language = booking.customer.language.split("-")[0] if booking.customer.language != None else ""
        
        guest.check_in = checkin.strftime("%Y-%m-%d %H:%M:%S")
        guest.check_out = checkout.strftime("%Y-%m-%d %H:%M:%S")
        guest.room = room
        guest.save()

        if booking.created:
            lock_code = get_code(project)

            err = guest.add_all_key_code(lock_code)
            if guest.email != "" and pmu.send_email:
                send_email_code(guest, lock_code, pmu)
    return booking, err

def delete_booking(pwu, booking):
    ext_id = get_ext_id(booking)
    guest = Guest.objects.filter(ext_id=ext_id, project_id=pwu.project_uuid, deleted=0).first()
    if guest != None:
        guest.delete()

def create_room(pmu, room, i):
    r = Room.objects.filter(project_uuid=pmu.project_uuid, number=room.number).first()
    if r == None:
        r = Room.objects.create(project_uuid=pmu.project_uuid, number=room.number, alias=room.number, order=i, uuid=new_ui_slug(Room))

def get_booking_list(pmu):
    av = Mews(pmu.client_token, pmu.access_token)
    result = av.get_bookings()
    #print(result)
    booking_list = []
    i = 0
    write_log("--- GET BOOKING LIST")
    for item in result:
        print("--1--")
        print(item)
        write_log(item)
        i += 1
        node = MewsBooking(item)

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

        node, err = create_booking(pmu, node, av)
        booking_list.append(node)
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

def get_room_list(pmu):
    av = Mews(pmu.client_token, pmu.access_token)
    result = av.get_resources()
    room_list = []
    i = 0
    for item in result:
        #print(item)
        room = MewsResource(item)
        room_list.append(room)
        create_room(pmu, room, i)
        i += 1
    return room_list

