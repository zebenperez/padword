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

import base64
import xml.etree.ElementTree as ET


try:
    API_URL = settings.AVAIBOOK_API_URL
except:
    #API_URL = "https://developer.siteminder.com"
    API_URL = "https://tpi-pmsx.preprod.siteminderlabs.com/core-api/pmses"

BOOKINGS_URL = "/__PMS__/hotels/__HOTEL__/reservation-import"

'''
    COMMONS
'''
def get_param(dic, key):
    return dic[key] if key in dic else ""

'''
    SOAP MANAGEMENT
'''
def roomraccoon_get_soap_response():
    soap_response = f"""<SOAP-ENV:Envelope
	    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
	    <SOAP-ENV:Header/>
	    <SOAP-ENV:Body>
		    <OTA_HotelResNotifRS
			    xmlns="http://www.opentravel.org/ota/2003/05" EchoToken="ed8835ff-6198-4f38-b589-3058397f677c" Version="1" TimeStamp="2024-07-06T15:27:47+00:00">
			    <Success/>
			    <HotelReservations>
				    <HotelReservation>
					    <ResGlobalInfo>
						    <HotelReservationIDs>
							    <HotelReservationID ResID_Source="PMS" ResID_Type="40" ResID_Value="ABC-1234567890"/>
						    </HotelReservationIDs>
					    </ResGlobalInfo>
				    </HotelReservation>
			    </HotelReservations>
		    </OTA_HotelResNotifRS>
	    </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>
    """
    return soap_response

def roomraccoon_get_soap_header(xml):
    try:
        namespaces = {
            'SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/',
            'wsse': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd'
        }

        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)

        root = ET.fromstring(xml)

        # Encontrar elementos usando namespaces
        username_elem = root.find('.//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}Username')
        password_elem = root.find('.//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}Password')

        if username_elem is not None and password_elem is not None:
            return {
                'username': username_elem.text,
                'password': password_elem.text
            }
        else:
            print("No se encontraron las credenciales en el header")
            return None

    except Exception as e:
        print(f"Error procesando SOAP header: {e}")
        return None

def roomraccoon_get_soap_body(xml_body):
    #print(f"📩 SOAP recibido de {username}:")
    #print(xml_body)

    # Parsear el XML
    root = ET.fromstring(xml_body)
    ns = {"soap": "http://schemas.xmlsoap.org/soap/envelope/"}

    # Extraer el Body SOAP
    body = root.find(".//soap:Body", ns)
    if body is None:
        raise ValueError("No se encontró el Body SOAP")

    # (Aquí podrías extraer tus parámetros específicos)
    contenido = ET.tostring(body, encoding="unicode")
    return contenido

def roomraccoon_parse_soap_reservation(xml_string):
    # Namespaces necesarios
    namespaces = {
        'SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/',
        'ota': 'http://www.opentravel.org/OTA/2003/05',
        'wsse': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd'
    }

    # Registrar los namespaces
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)

    try:
        root = ET.fromstring(xml_string)

        # Extraer datos de la reserva
        reservation_data = {}

        # Información básica de la reserva
        hotel_res = root.find('.//{http://www.opentravel.org/OTA/2003/05}HotelReservation')
        if hotel_res is not None:
            reservation_data['status'] = hotel_res.get('ResStatus')
            reservation_data['create_date'] = hotel_res.get('CreateDateTime')
            reservation_data['modify_date'] = hotel_res.get('LastModifyDateTime')
        
        # Unique ID
        unique_id = root.find('.//{http://www.opentravel.org/OTA/2003/05}UniqueID')
        if unique_id is not None:
            reservation_data['unique_id'] = unique_id.get('ID')
        

        # Buscar todos los RoomStay
        room_stays = root.findall('.//{http://www.opentravel.org/OTA/2003/05}RoomStay')

        # Lista para almacenar los datos de todas las habitaciones
        reservation_data['rooms'] = []

        # Iterar sobre cada RoomStay
        for room_stay in room_stays:
            room_data = {}
    
            # Tipo de habitación
            room_type = room_stay.find('.//{http://www.opentravel.org/OTA/2003/05}RoomType')
            if room_type is not None:
                room_data['room_id'] = room_type.get('RoomID')
                room_data['room_type'] = room_type.get('RoomType')
                room_data['room_type_code'] = room_type.get('RoomTypeCode')
                room_data['room_status'] = room_type.get('RoomStatus')
    
            # Fechas de estadía
            time_span = room_stay.find('.//{http://www.opentravel.org/OTA/2003/05}TimeSpan')
            if time_span is not None:
                room_data['check_in'] = time_span.get('Start')
                room_data['check_out'] = time_span.get('End')
    
            # Total
            total = room_stay.find('.//{http://www.opentravel.org/OTA/2003/05}Total')
            if total is not None:
                room_data['amount_before_tax'] = total.get('AmountBeforeTax')
                room_data['amount_after_tax'] = total.get('AmountAfterTax')
                room_data['currency'] = total.get('CurrencyCode')
    
            # Total
            ns = {'ota': 'http://www.opentravel.org/OTA/2003/05'}
            room_guest = room_stay.find('.//ota:ResGuestRPHs/ota:ResGuestRPH', ns)
            if room_guest is not None:
                room_data['guest_rph'] = room_guest.get('RPH')
 
            # Agregar los datos de esta habitación a la lista
            reservation_data['rooms'].append(room_data)

#        # Información de la habitación
#        room_stay = root.find('.//{http://www.opentravel.org/OTA/2003/05}RoomStay')
#        if room_stay is not None:
#            # Tipo de habitación
#            room_type = room_stay.find('.//{http://www.opentravel.org/OTA/2003/05}RoomType')
#            if room_type is not None:
#                reservation_data['room_id'] = room_type.get('RoomID')
#                reservation_data['room_type'] = room_type.get('RoomType')
#                reservation_data['room_type_code'] = room_type.get('RoomTypeCode')
#            
#            # Fechas de estadía
#            time_span = room_stay.find('.//{http://www.opentravel.org/OTA/2003/05}TimeSpan')
#            if time_span is not None:
#                reservation_data['check_in'] = time_span.get('Start')
#                reservation_data['check_out'] = time_span.get('End')
#            # Total
#            total = room_stay.find('.//{http://www.opentravel.org/OTA/2003/05}Total')
#            if total is not None:
#                reservation_data['amount_before_tax'] = total.get('AmountBeforeTax')
#                reservation_data['amount_after_tax'] = total.get('AmountAfterTax')
#                reservation_data['currency'] = total.get('CurrencyCode')
        
        # Información del huésped
        #ns = {'ota': 'http://www.opentravel.org/OTA/2003/05'}
        #profile = root.find( './/ota:ResGuests/ota:ResGuest/ota:Profiles/ota:ProfileInfo/ota:Profile', ns)
        #if profile == None:
        profile = root.find('.//{http://www.opentravel.org/OTA/2003/05}Profile')
        if profile is not None:
            customer = profile.find('.//{http://www.opentravel.org/OTA/2003/05}Customer')
            if customer is not None:
                person_name = customer.find('.//{http://www.opentravel.org/OTA/2003/05}PersonName')
                if person_name is not None:
                    reservation_data['guest_first_name'] = person_name.find('.//{http://www.opentravel.org/OTA/2003/05}GivenName').text
                    reservation_data['guest_last_name'] = person_name.find('.//{http://www.opentravel.org/OTA/2003/05}Surname').text
                
                telephone = customer.find('.//{http://www.opentravel.org/OTA/2003/05}Telephone')
                if telephone is not None:
                    reservation_data['guest_phone'] = telephone.get('PhoneNumber')
                
                email = customer.find('.//{http://www.opentravel.org/OTA/2003/05}Email')
                if email is not None:
                    reservation_data['guest_email'] = email.text
        

        ns = {'ota': 'http://www.opentravel.org/OTA/2003/05'}
        reservation_data['guests'] = []
        res_guests = root.findall('.//ota:ResGuests/ota:ResGuest', ns)
        # Fallback por si el namespace no está aplicado correctamente
        if not res_guests:
            res_guests = root.findall('.//{http://www.opentravel.org/OTA/2003/05}ResGuest')

        for res_guest in res_guests:
            guest_data = {}
            # Obtener ResGuestRPH
            guest_data['res_guest_rph'] = res_guest.get('ResGuestRPH')
            profile = res_guest.find('.//{http://www.opentravel.org/OTA/2003/05}Profile')
            if profile is not None:
                customer = profile.find('.//{http://www.opentravel.org/OTA/2003/05}Customer')
                if customer is not None:
                    person_name = customer.find('.//{http://www.opentravel.org/OTA/2003/05}PersonName')
                    if person_name is not None:
                        given_name = person_name.find('.//{http://www.opentravel.org/OTA/2003/05}GivenName')
                        surname = person_name.find('.//{http://www.opentravel.org/OTA/2003/05}Surname')

                        if given_name is not None:
                            guest_data['guest_first_name'] = given_name.text
                        if surname is not None:
                            guest_data['guest_last_name'] = surname.text
                    telephone = customer.find('.//{http://www.opentravel.org/OTA/2003/05}Telephone')
                    if telephone is not None:
                        guest_data['guest_phone'] = telephone.get('PhoneNumber')
                    email = customer.find('.//{http://www.opentravel.org/OTA/2003/05}Email')
                    if email is not None:
                        guest_data['guest_email'] = email.text
            reservation_data['guests'].append(guest_data)

        # Información del hotel
        basic_property = root.find('.//{http://www.opentravel.org/OTA/2003/05}BasicPropertyInfo')
        if basic_property is not None:
            reservation_data['hotel_code'] = basic_property.get('HotelCode')
        
        # Comentarios
        comment = root.find('.//{http://www.opentravel.org/OTA/2003/05}Comment/{http://www.opentravel.org/OTA/2003/05}Text')
        if comment is not None:
            reservation_data['comments'] = comment.text
        
        return reservation_data
        #return { 'reservation': reservation_data }
    except ET.ParseError as e:
        return {'error': f'Error parsing XML: {str(e)}'}

    #print(result)

'''
    CLASSES AND RESERVATION
'''
class RoomRaccoomAPIError(Exception):
    def __init__(self, menssage='Invalid Parameter'):
        self.menssage=menssage

    def __str__(self):
        return 'Error: {}'.format(self.menssage)

class RoomRaccoom():
    def __init__(self, username, password, token, pms, hotel):
        self.username = username
        self.password = password
        self.token = token
        self.pms = pms
        self.hotel = hotel
    
    def __send_request__(self, _url_request, _params=""):
        try:
            _headers = {}
            _headers['Accept'] = 'application/json'
            _headers['Authorization'] = 'Basic {}:{}'.format(self.username, self.password)
            _headers['X-SM-TRACE-TOKEN'] = '{}'.format(self.token)
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
            _headers['Authorization'] = 'Basic {}:{}'.format(self.username, self.password)
            _headers['X-SM-TRACE-TOKEN'] = '{}'.format(self.token)
            _response = requests.post(_url_request, headers=_headers, json=_json)
            #_response.raise_for_status()
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
            _url = BOOKINGS_URL.replace("__PMS__", self.pms).replace("__HOTEL__", self.hotel)
            _url_request = "{}{}".format(API_URL, _url)
            #params = {
            #    "dateType": "checkIn",
            #    "fromDate": "2025-07-01",
            #    "toDate": "2025-07-30"
            #}
            params = {}
            dic = self.__send_post_request__(_url_request, params).json()
            print(dic)
            return dic
        except Exception as err:
            raise RoomRaccoomAPIError(menssage=err)

#class RoomRaccoonBookingRoom():
#    def __init__(self, dic):
#        self.room_id = get_param(dic, "room_id")
#        self.room_type = get_param(dic, "room_type")
#        self.room_type_code = get_param(dic, "room_type_code")
#        self.check_in = get_param(dic, "check_in")
#        self.check_out = get_param(dic, "check_out")

class RoomRaccoonBooking():
    def __init__(self, dic, guest, room):
        self.id = get_param(dic, "unique_id")
        self.status = get_param(dic, "status")

        self.guest_name = get_param(guest, "guest_first_name")
        self.guest_last_name = get_param(guest, "guest_last_name")
        self.guest_phone = get_param(guest, "guest_phone")
        self.guest_email = get_param(guest, "guest_email")

        self.hotel_code = get_param(dic, "hotel_code")
        self.comments = get_param(dic, "comments")

        self.room_id = get_param(room, "room_id")
        self.room_type = get_param(room, "room_type")
        self.room_type_code = get_param(room, "room_type_code")
        self.check_in = get_param(room, "check_in")
        self.check_out = get_param(room, "check_out")

        self.created = False


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

def guest_is_changed(guest, room, checkin, checkout):
    gc_in = guest.check_in.strftime("%Y-%m-%d %H:%M:%S")
    gc_out = guest.check_out.strftime("%Y-%m-%d %H:%M:%S")
    c_in = checkin.strftime("%Y-%m-%d %H:%M:%S")
    c_out = checkout.strftime("%Y-%m-%d %H:%M:%S")
    return True if gc_in != c_in or gc_out != c_out or guest.room != room else False

def create_booking(pru, booking, f):
    checkin = get_date(booking.check_in, None)
    checkout = get_date(booking.check_out, None)
    room = booking.room_id
    room_ex = room_exist(pru.project_uuid, room)
    err = ""

    f.write("\n[LOG]: ROOM {} {}".format(room, room_ex))
    f.write("\n[LOG]: GUEST {} {}".format(booking.guest_name, booking.guest_last_name))
    f.write("\n[LOG]: STATUS {}".format(booking.status))
    if room_ex:
        f.write("\n[LOG]: CREA LA RESERVA")

        ext_id = f'{booking.id}-{booking.room_id}'
        #ext_id = f'{booking.id}'
        guest = Guest.objects.filter(ext_id=ext_id, project_id=pru.project_uuid, deleted=0).first()
        change_booking = False
        if guest == None:
            guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=ext_id, project_id=pru.project_uuid)
            booking.created = True
        else:
            change_booking = guest_is_changed(guest, room, checkin, checkout)

        f.write("\n[LOG]: ACTUALIZA LA RESERVA")

        guest.name = f"{booking.guest_name}"
        guest.surname = f"{booking.guest_last_name}"
        guest.mobile = booking.guest_phone
        guest.email = booking.guest_email
        guest.check_in = checkin
        guest.check_out = checkout
        guest.room = room
        guest.save()

        if booking.created:
            #lock_code = guest.mobile[-4:]
            lock_code = ''.join([random.choice(string.digits) for i in range(4)])
            err = guest.add_all_key_code(lock_code)
            #av.send_pwa_link(guest.ext_id, lock_code, guest.pwa_link)
        elif change_booking:
            #time.sleep(3)
            #msg += "\n MODIFICADA: {}".format(guest.ext_id)
            guest.change_room(room)

        return guest, err
    return None, err

def remove_booking(pru, booking, f):
    f.write("\n[LOG]: BORRANDO RESERVAS")
    guest_list = Guest.objects.filter(ext_id=f"{booking.id}-{booking.room_id}", project_id=pru.project_uuid, deleted=0)
    for guest in guest_list:
        f.write("\n[LOG]: BORRANDO RESERVA {}".format(guest.ext_id))
        #msg += "\n -- Borrando: {}".format(guest.ext_id)
        guest.delete_soft()

def get_booking_list():
    from .models import ProjectRoomraccoonUser
    pru = ProjectRoomraccoonUser.objects.filter(project_uuid='ccd38078-b710-eb58-b270-5926c27d9077').first()
    av = RoomRaccoom(pru.username, pru.password, pru.token, pru.pms, pru.hotel)
    result = av.get_bookings()
    #print(result)
    booking_list = []
    for item in result:
        node = RoomRaccoonBooking(item)
        booking_list.append(node)
        print(node)
        #create_booking(pau, node, av)
        #if node.status == "CONFIRMED":
        #    guest, err = create_booking(pau, node, av)
        #elif node.status == "CANCELLED":
        #    delete_booking(pau, node)
    return booking_list

def get_action(st):
    create_list = ["Reserved", "In-house"]
    cancel_list = ["Cancelled", "Checked-Out", "Checked-out"]
    if st in create_list:
        return "Manage"
    if st in cancel_list:
        return "Cancel"

def clean_booking(booking_id, rooms, pru):
    guest_list = Guest.objects.filter(ext_id__startswith=f'{booking_id}-', project_id=pru.project_uuid, deleted=0)
    g_ids = [item.room for item in guest_list]
    r_ids = [item["room_id"] for item in rooms]
    res_list = list(set(g_ids) - set(r_ids))
    for item in res_list:
        g = Guest.objects.filter(ext_id=f'{booking_id}-{item}', project_id=pru.project_uuid, deleted=0).first()
        if g != None:
            g.delete_soft()

def get_guest(booking, room):
    try:
        for item in booking["guests"]:
            if item["res_guest_rph"] == room["guest_rph"]:
                return item
    except:
        pass
    return {
        "guest_first_name": booking["guest_first_name"], 
        "guest_last_name": booking["guest_last_name"], 
        "guest_phone": booking["guest_phone"], 
        "guest_email": booking["guest_email"] 
    }

def roomraccoon_manage_booking(pru, booking, f):
    #av = RoomRaccoom(pau.uuid, pau.token)
    err = ""
    clean_booking(booking["unique_id"], booking["rooms"], pru)
    for item in booking["rooms"]:
        guest_node = get_guest(booking, item)
        node = RoomRaccoonBooking(booking, guest_node, item)
        f.write("\n[LOG]: MANAGE BOOKING")
        action = get_action(node.status)
        #action = get_action(item["room_status"])
        if action == "Manage":
            guest, err = create_booking(pru, node, f)
        if action == "Cancel":
            remove_booking(pru, node, f)
    return err

    #if guest != None:
    #    send_link(pau, guest)

#def send_link(pau, guest):
#    resp = "---"
#    av = RoomRaccoom(pau.uuid, pau.token)
#    resp = av.send_pwa_link(guest.ext_id, "", guest.pwa_link)
#    return resp

