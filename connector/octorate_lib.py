from django.conf import settings
from datetime import datetime, timedelta
from web.models import Room
from guest.models import Guest
from padword.commons import new_ui_slug, get_today_ini

import requests
import hashlib
import urllib
import json
import random
import string
import os

import base64
import xml.etree.ElementTree as ET


try:
    API_URL = settings.OCTORADE_API_URL
except:
    API_URL = "https://api.octorate.com/connect/rest/v1"

LOGIN_URL = "/identity/apilogin"
TOKEN_URL = "/identity/token"
REFRESH_URL = "/identity/refresh"
BOOKINGS_URL = "/reservation"
ROOMS_URL = "/pms"

'''
    COMMONS
'''
def get_param(dic, key):
    return dic[key] if key in dic else ""

def write_log(result):
    f = open(os.path.join(settings.BASE_DIR, "octorate.log"), "a", encoding='utf-8')
    f.write("{}\n".format(result))
    f.close()

#def code_payload(booking, meta_id, code, link):
#    return {
#        "status": "CONFIRMED",
#        "guests": [
#            {
#                #"id": 123123,
#                "type": booking.guest.type,                        
#                "givenName": booking.guest.given_name,
#                "familyName": booking.guest.family_name,
#                "customerName": booking.guest.customer_name,
#                "checkin": booking.guest.checkin,
#                "checkout": booking.guest.checkout
#                #"sex": "MALE",
#            }
#        ],
#        "channelId": booking.channel_id,                           
#        "product": booking.product,
#        "checkin": f'{booking.checkin.replace(" ", "T")}Z',
#        "checkout": f'{booking.checkout.replace(" ", "T")}Z',
#        #"createTime": booking.create_time,
#        #"updateTime": booking.update_time,
#        "roomGross": booking.room_gross,
#        "totalGuest": booking.total_guest,
#        "totalChildren": booking.total_children,
#        "totalInfants": booking.total_infants,
#        "roomCode": {"code": code},
#        "metaData": [
#            {
#                "id": meta_id,
#                "labelText": "DigitalKey",
#                "metaKey": "PadwordKey",
#                "metaDataType": "LINK",
#                "value": link
#            }
#        ],
#    }

def code_payload(booking, meta_id, code, link):
    return {
        "status": "CONFIRMED",
        "channelId": booking.channel_id,                           
        "product": booking.product,
        "checkin": f'{booking.checkin.replace(" ", "T")}Z',
        "checkout": f'{booking.checkout.replace(" ", "T")}Z',
        "roomCode": {"code": code},
        "metaData": [
            {
                "labelText": "DigitalKey",
                "metaKey": "PadwordKey",
                "metaDataType": "LINK",
                "value": link
            }
        ],
    }

class OctorateAPIError(Exception):
    def __init__(self, menssage='Invalid Parameter'):
        self.menssage=menssage

    def __str__(self):
        return 'Error: {}'.format(self.menssage)

class Octorate():
    def __init__(self, client_id, client_secret, token, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.token = token
        self.ids = ""
    
    def __send_request__(self, _url_request, _params=""):
        try:
            _headers = {}
            _headers['Accept'] = 'application/json'
            _headers['Authorization'] = 'Bearer {}'.format(self.token)
            if _params != "":
                _response = requests.get(_url_request, headers=_headers, params=_params)
            else:
                _response = requests.get(_url_request, headers=_headers)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise OctorateAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise OctorateAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise OctorateAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise OctorateAPIError(menssage=err)

    def __send_post_request__(self, _url_request, _json):
        try:
            _headers = {}
            _headers['Content-Type'] = 'application/x-www-form-urlencoded'
            _response = requests.post(_url_request, headers=_headers, data=_json)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise OctorateAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise OctorateAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise OctorateAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise OctorateAPIError(menssage=err)

    def __send_post_token_request__(self, _url_request, _json):
        try:
            _headers = {}
            _headers['Authorization'] = 'Bearer {}'.format(self.token)
            _headers['Content-Type'] = 'application/json'
            _response = requests.patch(_url_request, headers=_headers, data=_json)
            return _response
        except requests.exceptions.HTTPError as errh:
            raise OctorateAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise OctorateAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise OctorateAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise OctorateAPIError(menssage=err)

    def __send_put_request__(self, _url_request, _json):
        try:
            _headers = {}
            _headers['Authorization'] = 'Bearer {}'.format(self.token)
            _headers['Content-Type'] = 'application/json'
            _response = requests.put(_url_request, headers=_headers, data=_json)
            return _response
        except requests.exceptions.HTTPError as errh:
            raise OctorateAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise OctorateAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise OctorateAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise OctorateAPIError(menssage=err)

    def __send_patch_request__(self, _url_request, _json):
        try:
            _headers = {}
            _headers['Authorization'] = 'Bearer {}'.format(self.token)
            _headers['Content-Type'] = 'application/json'
            _response = requests.patch(_url_request, headers=_headers, data=_json)
            return _response
        except requests.exceptions.HTTPError as errh:
            raise OctorateAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise OctorateAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise OctorateAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise OctorateAPIError(menssage=err)

    def get_bookings(self, property_id, i_date, e_date):
        try:
            _url_request = f'{API_URL}{BOOKINGS_URL}/{property_id}'
            today = datetime.today()
            params = {
                "startDate": i_date.strftime("%Y-%m-%d"),
                "endDate": e_date.strftime("%Y-%m-%d"),
                "type": "CHECKIN",
                "status": "CONFIRMED"
            }
            dic = self.__send_request__(_url_request, params).json()
            items = dic["data"]
            return items
        except Exception as err:
            raise OctorateAPIError(menssage=err)

    def get_rooms(self, property_id):
        try:
            _url_request = f'{API_URL}{ROOMS_URL}'
            params = {}
            dic = self.__send_request__(_url_request, params).json()
            items = dic["data"]
            return items
        except Exception as err:
            print(err)
            raise OctorateAPIError(menssage=err)

    def get_token(self, redirect_uri, code):
        try:
            _url_request = "{}{}".format(API_URL, TOKEN_URL)
            payload = {
                "client_id": self.client_id, 
                "client_secret": self.client_secret,
                "redirect_uri": redirect_uri, 
                "code": code
            }
            dic = self.__send_post_request__(_url_request, payload).json()
            items = dic["data"]
            return items
        except Exception as err:
            raise OctorateAPIError(menssage=err)

    def get_new_token(self):
        try:
            _url_request = "{}{}".format(API_URL, REFRESH_URL)
            payload = {
                "refresh_token": self.refresh_token, 
                "client_id": self.client_id, 
                "client_secret": self.client_secret
            }
            dic = self.__send_post_request__(_url_request, payload).json()
            self.token = dic["access_token"]
            return self.token
        except Exception as err:
            print(err)
            raise OctorateAPIError(menssage=err)

    def send_code(self, property_id, booking, meta_id, code, link):
        try:
            booking_id = booking.id.split("_")[0]
            _url_request = f'{API_URL}{BOOKINGS_URL}/{property_id}/{booking_id}'
            #today = datetime.today()
            #if meta_id != "":
            #    meta_data = [{"id":meta_id, "labelText":"DigitalKey", "metaKey":"PadwordKey", "metaDataType":"LINK", "value": link}]
            #else:
            #    meta_data = [{"labelText":"DigitalKey", "metaKey":"PadwordKey", "metaDataType":"LINK", "value": link}]
            #params = {
            #    "roomCode": {"code": code},
            #    "metaData": meta_data,
            #    "status": "CONFIRMED"
            #}
            c = booking.room_code if booking.room_code != "" else code
            params = code_payload(booking, meta_id, c, link)
            msg = f"\n SEND CODE URL: {_url_request}"
            msg += f"\n SEND CODE PARAMS: {params}"
            #print("--1--")
            #print(_url_request)
            #print(params)
            dic = self.__send_patch_request__(_url_request, json.dumps(params)).json()
            #print(dic)
            return dic, msg
            #items = dic["data"]
            #return items
        except Exception as err:
            raise OctorateAPIError(menssage=err)

    def add_payment(self, property_id, booking_id, amount, paymentMode="PREPAID"):
        try:
            _url_request = f'{API_URL}{BOOKINGS_URL}/{property_id}/{booking_id}/payment'
            today = datetime.today()
            params = {
                "referenceTime": today.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "paymentMode": paymentMode,
                "amount": amount 
            }
            dic = self.__send_post_token_request__(_url_request, json.dumps(params)).json()
            #print(dic)
            return dic
        except Exception as err:
            raise OctorateAPIError(menssage=err)

class OctorateGuest():
    def __init__(self, dic):
        self.type = get_param(dic, "type")
        self.given_name = get_param(dic, "givenName")
        self.family_name = get_param(dic, "familyName")
        self.customer_name = get_param(dic, "customerName")
        self.checkin = get_param(dic, "checkin")
        self.checkout = get_param(dic, "checkout")
        #self.sex = get_param(dic, "sex")
 
class OctorateBooking():
    def __init__(self, dic, guest, room_code):
        self.id = "{}_{}".format(get_param(dic, "id"), get_param(dic, "refer"))
        self.status = get_param(dic, "status")
        self.name = get_param(dic, "firstName")
        self.surname = get_param(dic, "lastName")
        self.checkin = get_param(dic, "checkin").replace("T", " ").split("Z")[0]
        self.checkout = get_param(dic, "checkout").replace("T", " ").split("Z")[0]
        self.room = get_param(dic, "pmsProduct")
        self.room_code = room_code

        self.email = get_param(guest, "email")
        self.phone = get_param(guest, "phone")
        self.language = get_param(guest, "language")

        self.channel_id = get_param(dic, "channelId")
        self.product = get_param(dic, "product")
        self.create_time = get_param(dic, "createTime")
        self.update_time = get_param(dic, "updateTime")
        self.room_gross = get_param(dic, "roomGross")
        self.total_guest = get_param(dic, "totalGuest")
        self.total_children = get_param(dic, "totalChildren")
        self.total_infants = get_param(dic, "totalInfants")

        self.guest = OctorateGuest(guest)

        self.created = False


class OctorateRoom():
    def __init__(self, dic):
        self.id = get_param(dic, "id")
        self.name = get_param(dic, "name")

'''
    FUNCTIONS
'''
def create_room(pou, room, index):
    r = Room.objects.filter(project_uuid=pou.project_uuid, number=room.id).first()
    if r != None:
        return r

    r =  Room.objects.create(project_uuid=pou.project_uuid, number=room.id)
    r.alias = room.name
    r.uuid = new_ui_slug(Room)
    r.order = index 
    r.save()

def room_exist(project_uuid, room):
    count = Room.objects.filter(project_uuid=project_uuid, number=room).count()
    return (count > 0)

def get_date(date):
    return datetime.strptime("{}".format(date), "%Y-%m-%d %H:%M:%S")

def get_code(pou, mobile=""):
    #return ''.join([random.choice(string.digits) for i in range(4)]) 
    return mobile.rstrip()[-4:] if pou.code_mobile and mobile != "" else ''.join([random.choice(string.digits) for i in range(4)]) 

def set_meta_id(pou, dic):
    try:
        if pou.meta_id == "":
            pou.meta_id = dic["metaData"][0]["id"]
            pou.save()
        return ""
    except Exception as e:
        return str(e)

def create_booking(pou, booking, oc):
    checkin = get_date(booking.checkin)
    checkout = get_date(booking.checkout)
    #today = datetime.today()
    today = get_today_ini()
    e_date = today + timedelta(pou.days)
    room_ex = room_exist(pou.project_uuid, booking.room)
    err = ""
    msg = ""

    if room_ex and booking.status == "CONFIRMED" and checkin <= e_date and checkin >= today:
        msg += "\n Entrando"
        #ext_id = get_ext_id(booking, bguest, room)
        ext_id = booking.id
        guest = Guest.objects.filter(ext_id=ext_id, project_id=pou.project_uuid, deleted=0).first()
        if guest == None:
            guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=ext_id, project_id=pou.project_uuid)
            booking.created = True
        
        guest.name = booking.name
        guest.surname = booking.surname
        guest.mobile = booking.phone
        guest.email = booking.email
        guest.language = booking.language
        
        guest.check_in = checkin
        guest.check_out = checkout
        guest.room = booking.room
        guest.save()
        msg += "\n Asignando: {} ({})".format(guest.room, guest.name)

        if booking.created:
            msg += "\n CREADA: {}".format(guest.ext_id)
            lock_code = get_code(pou, guest.mobile)
            msg += "-- CODE: {} - mobile {} - code mobile{}".format(lock_code, guest.mobile, pou.code_mobile)
            #print(lock_code)
            err = guest.add_all_key_code(lock_code)
            msg += "\n {}".format(err)
            #res, msg2 = oc.send_code(pou.property_id, booking.id.split("_")[0], pou.meta_id, lock_code, guest.pwa_link)
            res, msg2 = oc.send_code(pou.property_id, booking, pou.meta_id, lock_code, guest.pwa_link)
            msg += "\n {}".format(msg2)
            msg += "\n {}".format(res)
            err = set_meta_id(pou, res)
            msg += "\n {}".format(err)
            #oc.ids += "{}:{},".format(room.name, guest.ext_id)
            #msg += send_booking_codes(pcu, av, booking.id)
    return msg


def get_token(pcu, ext_id):
    msg = ""
    oc = Octorate(pcu.client_id, pcu.secret, pcu.token, pcu.refresh)
    #client_id = "public_8a17175ce23b4f26888e3c2f1f355b9c"
    #client_secret = "secret_efbdad0123d04470a9dac99228e139a0SXGFNUSURY"
    redirect_uri = "http%3A%2F%2Fpaddev.shidix.es%2Fconnector%2Foctorate%2Fupdate-token%2F'" 
    code = "487165"
    oc.get_token(redirect_uri, code)
    return ""


def get_booking_list(pou):
    oc = Octorate(pou.client_id, pou.secret, pou.token, pou.refresh)
    token = oc.get_new_token()
    pou.token = token
    pou.save()
    today = datetime.today()
    e_date = today + timedelta(pou.days)
    result = oc.get_bookings(pou.property_id, today, e_date)
    booking_list = []
    i = 0
    write_log(f"---------------------------------------------")
    write_log(f"CREANDO RESERVAS {datetime.now()}")
    for item in result:
        #print(item)
        write_log(f"{item}")
        #print("--------------")
        i += 1
        guest = item["guests"][0] if "guests" in item and len(item["guests"]) > 0 else []
        room_code = item["roomCode"]["code"] if "roomCode" in item  and "code" in item["roomCode"] else ""
        write_log(f"ROOM CODE: {room_code}")
        if "roomCode" in item:
            write_log(f"ROOM CODE 111: {item['roomCode']}")
            if "code" in item["roomCode"]:
                write_log(f"ROOM CODE 222: {item['roomCode']['code']}")
        node = OctorateBooking(item, guest, room_code)
        msg = create_booking(pou, node, oc)
        booking_list.append(node)
        write_log(f"{msg}")
    return booking_list

def get_room_list(pou):
    oc = Octorate(pou.client_id, pou.secret, pou.token, pou.refresh)
    result = oc.get_rooms(pou.property_id)
    room_list = []
    i = 0
    for item in result:
        i += 1
        node = OctorateRoom(item)
        create_room(pou, node, i)
        room_list.append(node)
    return room_list


