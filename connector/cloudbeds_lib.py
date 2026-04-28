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
import time

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
WEBHOOK_DELETE_URL = "deleteWebhook"
CUSTOM_FIELD_URL = "postCustomField"
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
        self.ids = ""
        self.send_codes = False
        #self.codes = ""
        #self.links = ""
    
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

    def __send_delete_request__(self, _url_request, _params=""):
        try:
            _headers = {}
            _headers['Accept'] = 'application/json'
            _headers['x-api-key'] = '{}'.format(self.token)
            if _params != "":
                _response = requests.delete(_url_request, headers=_headers, params=_params)
            else:
                _response = requests.delete(_url_request, headers=_headers)
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


    def get_bookings(self, checkin, checkout, status=CONFIRM_STATE):
        try:
            _url_request = "{}{}".format(API_URL, BOOKINGS_URL)
            params = {
                "checkInFrom": checkin,
                "checkInTo": checkout,
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

    def get_rooms(self, property_id):
        try:
            _url_request = "{}{}?propertyIDs={}&pageNumber=1&pageSize=500".format(API_URL, ROOMS_URL, property_id)
            #_url_request = "{}{}".format(API_URL, ROOMS_URL)
            #params = {
            #    "pageNumber": "10",
            #    "pageSize": "100"
            #}
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
            return str(dic)
        except Exception as err:
            raise CloudbedsAPIError(menssage=err)

    def delete_webhook(self, property_id, subs_id):
        try:
            _url_request = "{}{}".format(API_URL, WEBHOOK_DELETE_URL)
            params = { "propertyID": property_id, "subscriptionID": subs_id }
            dic = self.__send_delete_request__(_url_request, params).json()
            return dic
        except Exception as err:
            raise CloudbedsAPIError(menssage=err)

    def set_custom_field(self, name):
        try:
            _url_request = "{}{}".format(API_URL, CUSTOM_FIELD_URL)
            params = {
                "name": name,
                "shortcode": name,
                "maxCharacters": 2000,
                "isPersonal": "False"
            }
            dic = self.__send_post_request__(_url_request, params).json()
            return str(dic)
        except Exception as err:
            raise CloudbedsAPIError(menssage=err)


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
        self.plate = ""
        custom_fields = get_param(dic, "customFields")
        try:
            for cf in custom_fields:
                if cf["customFieldName"] == "Matricula":
                    self.plate = cf["customFieldValue"]
        except:
            pass

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
        self.subreservation_id = get_param(dic, "subReservationID")
        self.check_in = ""
        self.check_out = ""


'''
    FUNCTIONS
'''
def get_ext_id(booking, guest, room):
    return "{}".format(room.subreservation_id)
    #return "{}".format(booking.id)
    #return "{}_{}_{}".format(booking.id, guest.id, room.id)

def get_code(pcu, mobile=""):
    return mobile.rstrip()[-4:] if pcu.code_mobile and mobile != "" else ''.join([random.choice(string.digits) for i in range(4)]) 

def get_date(date, hour, minute):
    return datetime.strptime("{} {}:{}".format(date, hour, minute), "%Y-%m-%d %H:%M")

def room_exist(project_uuid, room):
    count = Room.objects.filter(project_uuid=project_uuid, number=room).count()
    return (count > 0)

def send_lock_code(pcu, guest, booking_id):
    lock_code = get_code(pcu, guest.mobile)
    err = guest.add_all_key_code(lock_code)
    av = Cloudbeds(pcu.token)
    av.set_booking_code(booking_id, "lockCode", lock_code)
    av.set_booking_code(booking_id, "lockLink", guest.pwa_link)

def create_booking(pcu, room, booking, bguest, av, ev=""):
    checkin = get_date(booking.start, pcu.ini_time.hour, pcu.ini_time.minute)
    checkout = get_date(booking.end, pcu.end_time.hour, pcu.end_time.minute)
    today = datetime.today()
    e_date = today + timedelta(pcu.days)
    r = room.id if room != None else "-1"
    room_ex = room_exist(pcu.project_uuid, r)
    err = ""
    msg = ""
    #msg += "\n Habitación: {} ({}) - {}".format(r, room_ex, booking.status)
    #msg += "\n Fechas: {} {} {}".format(checkin, e_date, today)

    if room_ex and (booking.status == "confirmed" or booking.status == "checked_in") and checkin <= e_date and checkin >= today:
        #msg += "\n Entrando"
        ext_id = get_ext_id(booking, bguest, room)
        msg += f"\n Ext_id: {ext_id}"
        guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
        msg += f"\n Guest: {guest}"
        if guest != None or ev == "reservation/created":
            if guest == None:
                guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=ext_id, project_id=pcu.project_uuid)
                booking.created = True
            
            gc_in = guest.check_in.strftime("%Y-%m-%d %H:%M:%S")
            gc_out = guest.check_out.strftime("%Y-%m-%d %H:%M:%S")
            c_in = checkin.strftime("%Y-%m-%d %H:%M:%S")
            c_out = checkout.strftime("%Y-%m-%d %H:%M:%S")
            change_booking = True if gc_in != c_in or gc_out != c_out or guest.room != r else False
            #msg += "\n Checkin {} == {}".format(gc_in, c_in)
            #msg += "\n Checkout {} == {}".format(gc_out, c_out)
            #msg += "\n Checkout {} == {}".format(guest.room, r)
            #msg += "\n Change Booking {}".format(change_booking)
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
            msg += f"\n Asignando: {guest.room} ({guest.name}) {booking.created} {change_booking}"

            if booking.plate != "":
                guest.add_plate(booking.plate)

            if booking.created:
                msg += "\n CREADA: {}".format(guest.ext_id)
                lock_code = get_code(pcu, guest.mobile)
                #msg += "-- CODE: {} - mobile {} - code mobile{}".format(lock_code, guest.mobile, pcu.code_mobile)
                #print(lock_code)
                if guest.lock_code == "":
                    err = guest.add_all_key_code(lock_code)
                    msg += "\n CODES: {}".format(err)
                av.send_codes = True
                #av.ids += "{}:{},".format(room.name, guest.ext_id)
                #av.ids = "{}:{},".format(room.name, guest.ext_id)
                #msg += send_booking_codes(pcu, av, booking.id)
                #msg += send_booking_codes(pcu, av, booking.id, room.name, guest)
                #av.codes += "{}:{} ".format(r, lock_code)
                #av.links += "{}:{} ".format(r, guest.pwa_link)
                #av.set_booking_code(booking.id, "lockCode", lock_code)
                #av.set_booking_code(booking.id, "lockLink", guest.pwa_link)
            elif change_booking:
                #time.sleep(3)
                msg += "\n MODIFICADA: {}".format(guest.ext_id)
                err = guest.change_room(r)
                msg += "\n CHANGE ROOM: {}".format(err)
                av.send_codes = True
    return msg

def create_room(pcu, room, index):
    r = Room.objects.filter(project_uuid=pcu.project_uuid, number=room.id).first()
    if r != None:
        return r

    r =  Room.objects.create(project_uuid=pcu.project_uuid, number=room.id)
    r.alias = room.name
    r.uuid = new_ui_slug(Room)
    r.order = index 
    r.save()

def get_booking_list(pcu):
    #get_or_create_booking(pcu, "8990638557302")
    #return []
    i_date = datetime.today()
    e_date = i_date + timedelta(pcu.days)
    av = Cloudbeds(pcu.token)
    result = av.get_bookings(i_date.strftime("%Y-%m-%d"), e_date.strftime("%Y-%m-%d"))
    booking_list = []
    i = 0
    for item in result:
        i += 1
        node = CloudbedsBooking(item)
        room_list = get_param(item, "rooms")
        for room in room_list:
            room_node = CloudbedsBookingRoom(room)
            guest = av.get_guest(room_node.guest_id)
            guest_node = CloudbedsGuest(guest)
            create_booking(pcu, room_node, node, guest_node, av, "reservation/created")
            node.rooms.append(room_node)
        booking_list.append(node)
    return booking_list

def get_room_list(pcu):
    av = Cloudbeds(pcu.token)
    result = av.get_rooms(pcu.property_id)
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
    result = "Adding reservation/created webhook <br/>"
    result += av.set_webhook("reservation", "created", pcu.property_id)
    result += "<br/>"
    result += "Adding reservation/status_changed webhook <br/>"
    result += av.set_webhook("reservation", "status_changed", pcu.property_id)
    result += "<br/>"
    result += "Adding reservation/dates_changed webhook <br/>"
    result += av.set_webhook("reservation", "dates_changed", pcu.property_id)
    result += "<br/>"
    result += "Adding reservation/accommodation_changed webhook <br/>"
    result += av.set_webhook("reservation", "accommodation_changed", pcu.property_id)
    result += "<br/>"
    result += "Adding reservation/deleted webhook <br/>"
    result += av.set_webhook("reservation", "deleted", pcu.property_id)
    result += "<br/>"
    #result += "Adding guest/accommodation_changed webhook <br/>"
    #result += av.set_webhook("guest", "accommodation_changed", pcu.property_id)
    #result += "<br/>"
    result += "Adding integration/appstate_changed webhook <br/>"
    result += av.set_webhook("integration", "appstate_changed", pcu.property_id)
    result += "<br/>"
    result += "Adding custom field 'lockCode' <br/>"
    result += av.set_custom_field("lockCode")
    result += "<br/>"
    result += "Adding custom field 'lockLink' <br/>"
    result += av.set_custom_field("lockLink")
    #print("-- Result: {}".format(result))
    return result

def manage_webhook_actions(pcu, obj):
    #random_time = random.uniform(4.0, 12.0)
    #time.sleep(random_time)
    msg = ""
    if obj["event"] == "reservation/created":
        msg = "\n-- Creada la reserva {}".format(obj["reservationID"])
        msg += get_or_create_booking(pcu, obj["reservationID"], obj["event"])

    if obj["event"] == "reservation/status_changed":
        msg = "\n-- Modificado el estado de la reserva {}".format(obj["reservationID"])
        msg += get_or_create_booking(pcu, obj["reservationID"], obj["event"])

    if obj["event"] == "reservation/dates_changed":
        msg = "\n-- Modificadas las fechas de la reserva {}".format(obj["reservationId"])
        msg += get_or_create_booking(pcu, obj["reservationId"], obj["event"])

    if obj["event"] == "reservation/accommodation_changed":
        msg = "\n-- Modificada la habitación de la reserva {}".format(obj["reservationId"])
        msg += get_or_create_booking(pcu, obj["reservationId"], obj["event"])

    if obj["event"] == "reservation/deleted":
        msg = "\n-- Eliminada la reserva {}".format(obj["reservationId"])
        msg += reservation_delete(pcu, obj)

    #if obj["event"] == "guest/accommodation_changed":
    #    msg = "\n-- Modificada la habitación del huésped {}".format(obj["reservationId"])
    #    msg += get_or_create_booking(pcu, obj["reservationId"], obj["event"])

    if obj["event"] == "integration/appstate_changed":
        disabled_connection(pcu, obj)
        msg = "\n-- Desconectada la propiedad {}".format(obj["propertyId"])
    return msg

def get_subreservation_dates(booking, sub_id):
    if "assigned" in booking:
        for node in booking["assigned"]:
            if node["subReservationID"] == sub_id:
                return node["startDate"], node["endDate"]
    return booking["startDate"], booking["endDate"]

def get_or_create_booking(pcu, ext_id, ev):
    if pcu == None:
        return "\n -- Objeto no encontrado"

    msg = ""
    av = Cloudbeds(pcu.token)
    booking = av.get_booking(ext_id)
    #print(booking)
    #msg += "\n {}".format(booking)
    node = CloudbedsBooking(booking)

    msg += "\n -- Estado: {}".format(node.status)
    if node.status == "canceled" or node.status == "check_out":
        #msg += "\n -- Cancelada."
        guest_list = Guest.objects.filter(ext_id__startswith=ext_id, project_id=pcu.project_uuid, deleted=0)
        for guest in guest_list:
            msg += "\n -- Borrando: {}".format(guest.ext_id)
            guest.delete_soft()
    else:
        guest_list = get_param(booking, "guestList")
        data_list = []
        for guest_id in guest_list:
            datas = guest_list[guest_id]
            #msg += "\n DATAS: {}".format(datas)
            guest_node = CloudbedsGuest2(datas)

            room_list = get_param(datas, "rooms")
            for room_data in room_list:
                node.start, node.end = get_subreservation_dates(booking, room_data["subReservationID"])
                room_node = CloudbedsRoom2(room_data)
                msg_g = create_booking(pcu, room_node, node, guest_node, av, ev)
                msg += "\n {}".format(msg_g)
                data_list.append(f"{room_node.name}:{room_node.subreservation_id}")
            break
        #Envío de códigos de reserva y subreservas
        msg += send_booking_codes(pcu, av, node.id, data_list)
        #msg += send_booking_codes(pcu, av, node.id)
    return msg

def reservation_delete(pcu, obj):
    ext_id = obj["reservationId"]
    msg = "\n -- Borrado de reservas"
    guest_list = Guest.objects.filter(ext_id__startswith=ext_id, project_id=pcu.project_uuid, deleted=0)
    for guest in guest_list:
        msg += "\n -- Borrado de subreserva: {}".format(guest.ext_id)
        guest.delete_soft()
    return msg

def remove_webhooks(pcu):
    res = ""
    av = Cloudbeds(pcu.token)
    result = av.get_webhook(pcu.property_id)
    if "data" in result:
        for r in result["data"]:
            av.delete_webhook(pcu.property_id, r["id"])
            res += f'Removing webhook {r} <br/>'
    return res
 
def disabled_connection(pcu, obj):
    prop_id = obj["propertyID"]

    av = Cloudbeds(pcu.token)
    result = av.get_webhook(pcu.property_id)
    if "data" in result:
        for r in result["data"]:
            av.delete_webhook(prop_id, r["id"])
 
    if obj["newState"] == "disabled":
        pcu.token = ""
        pcu.property_id = ""
        pcu.save()
    return ""

def send_booking_codes(pcu, av, booking_id, data_list):
    msg = ""
    msg = f"\n -- Send Codes: {av.send_codes} --"
    if av.send_codes:
        codes = ""
        links = ""
        #guest_list = av.ids.split(",")
        msg += f"\n -- Envío de códigos: {data_list} --"
        for data in data_list:
            if ":" in data:
                try:
                    datas = data.split(":")
                    msg += f"\n -- Procesando: {datas}"
                    room = datas[0]
                    ext_id = datas[1]
                    if ext_id != "":
                        guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
                        if guest != None:
                            #lock_code = get_code(pcu, guest.mobile)
                            #msg += "-- CODE: {} - mobile {} - code mobile{}".format(lock_code, guest.mobile, pcu.code_mobile)
                            #err = guest.add_all_key_code(lock_code)
                            #msg += "\n {}".format(err)
                            #if not "Error" in err:
                            codes += "{}:{} ".format(room, guest.lock_code)
                            links += "{}:{} ".format(room, guest.pwa_link)
                except Exception as e:
                    msg += "\n -- Error: {}".format(e)
        if codes != "":
            msg += "\n -- Enviando códigos: {}".format(codes)
            msg += "\n -- Enviando enlaces: {}".format(links)
            av.set_booking_code(booking_id, "lockCode", codes)
            av.set_booking_code(booking_id, "lockLink", links)
            msg += "\n -- Códigos enviados"
    return msg

#def send_booking_codes(pcu, av, booking_id):
#    codes = ""
#    links = ""
#    guest_list = av.ids.split(",")
#    msg = f"\n -- Envío de códigos {av.ids} --"
#    for data in guest_list:
#        if ":" in data:
#            try:
#                datas = data.split(":")
#                room = datas[0]
#                ext_id = datas[1]
#                if ext_id != "":
#                    guest = Guest.objects.filter(ext_id=ext_id, project_id=pcu.project_uuid, deleted=0).first()
#                    if guest != None:
#                        lock_code = get_code(pcu, guest.mobile)
#                        #msg += "-- CODE: {} - mobile {} - code mobile{}".format(lock_code, guest.mobile, pcu.code_mobile)
#                        err = guest.add_all_key_code(lock_code)
#                        msg += "\n {}".format(err)
#                        if not "Error" in err:
#                            codes += "{}:{} ".format(room, lock_code)
#                            links += "{}:{} ".format(room, guest.pwa_link)
#            except Exception as e:
#                msg = "\n -- Error: {}".format(e)
#    if codes != "":
#        msg += "\n -- Enviando códigos: {}".format(codes)
#        msg += "\n -- Enviando enlaces: {}".format(links)
#        av.set_booking_code(booking_id, "lockCode", codes)
#        av.set_booking_code(booking_id, "lockLink", links)
#        msg += "\n -- Códigos enviados"
#    return msg

#def send_booking_codes(pcu, av, booking_id, room, guest):
#    codes = ""
#    links = ""
#    msg = "\n -- Envío de códigos"
#    try:
#        if guest != None:
#            lock_code = get_code(pcu, guest.mobile)
#            #msg += "-- CODE: {} - mobile {} - code mobile{}".format(lock_code, guest.mobile, pcu.code_mobile)
#            #print(lock_code)
#            err = guest.add_all_key_code(lock_code)
#            msg += "\n {}".format(err)
#            if not "Error" in err:
#                codes += "{}:{} ".format(room, lock_code)
#                links += "{}:{} ".format(room, guest.pwa_link)
#    except Exception as e:
#        msg = "\n -- Error: {}".format(e)
#    if codes != "":
#        msg += "\n -- Enviando códigos: {}".format(codes)
#        av.set_booking_code(booking_id, "lockCode", codes)
#        av.set_booking_code(booking_id, "lockLink", links)
#        msg += "\n -- Códigos enviados"
#    return msg
#

