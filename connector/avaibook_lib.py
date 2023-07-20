import requests
import hashlib
import urllib

API_URL = "https://api.avaibook.biz/api/partner/"
BOOKINGS_URL = "booking/bookings"
ACCOMMODATIONS_URL = "accommodations"

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

class AvaibookBooking():
    def __init__(self, dic):
        self.id = get_param(dic, "id")
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
    return booking_list

def get_accommodation_list(pau):
    av = Avaibook(pau.uuid, pau.token)
    result = av.get_accommodations()
    item_list = []
    for item in result:
        unit_list = []
        for u in item["units"]:
            unit = AvaibookAccommodationUnit(u)
            unit_list.append(unit)
        loc = AvaibookAccommodationLocation(item["location"]) if "location" in item else {}
        node = AvaibookAccommodation(item, loc, unit_list)
        item_list.append(node)
    return item_list

