from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
#from zeep.settings import Settings
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from .models import ProjectAvantioUser
from guest.models import Guest
from padword.commons import get_or_none, new_ui_slug

WSDL = 'http://ws.avantio.com/soap/vrmsInputServices.php?wsdl'


class AvantioBookingClient:
    def __init__(self, name, surname, dni, address, locality, postcode, city, country, country_code, phone, phone2, email):
        self.name = name
        self.surname = surname
        self.dni = dni
        self.address = address
        self.locality = locality
        self.postcode = postcode
        self.city = city
        self.country = country
        self.country_code = country_code
        self.phone = phone
        self.phone2 = phone2
        self.email = email

class AvantioBooking:
    def __init__(self, start_time, end_time, start_date, end_date, booking_date, booking_code, localizator, accommodation_code, user_code, client):
        self.start_time = start_time
        self.end_time = end_time
        self.start_date = start_date
        self.end_date = end_date
        self.booking_date = booking_date
        self.booking_code = booking_code
        self.localizator = localizator
        self.accommodation_code = accommodation_code
        self.user_code = user_code
        self.client = client
        self.created = False
    
class AvantioNotification:
    def __init__(self, booking_code, localizator):
        self.booking_code = booking_code
        self.localizator = localizator
 
class ShAvantio:
    def __init__(self, username, password):
        self.credentials = {"Credentials": {"UserName": username, "Password": password}}
        #self.settings = Settings(strict=False, xml_huge_tree=True, xsd_ignore_sequence_order=True)
        self.client = Client(WSDL, transport=Transport(session=Session()))

    def get_param(self, b, param):
        try:
            return b.find(param).text
        except Exception as e:
            #print(e)
            return ""

    def get_booking_list(self, start_date="", end_date=""):
        booking_list = []
        with self.client.settings(raw_response=True):
            params = self.credentials
            if start_date != "":
                params["StartDate"] = start_date
            if end_date != "":
                params["EndDate"] = end_date
            #resp = self.client.service.GetBookingList(**self.credentials)
            #print(params)
            resp = self.client.service.GetBookingList(**params)
            #print("--2--")
            #print(resp.content)
            soup = BeautifulSoup(resp.content.decode("utf-8"), 'xml')
            #print(len(soup.find_all('ns2:Booking')))
            for b in soup.find_all('ns2:Booking'):
                name = self.get_param(b, 'ns2:Name')
                surname = self.get_param(b, 'ns2:Surname')
                dni = self.get_param(b, 'ns2:DNI')
                address = self.get_param(b, 'ns2:Address')
                locality = self.get_param(b, 'ns2:Locality')
                postcode = self.get_param(b, 'ns2:PostCode')
                city = self.get_param(b, 'ns2:City')
                country = self.get_param(b, 'ns2:Country')
                country_code = self.get_param(b, 'ns2:ISOCountryCode')
                phone = self.get_param(b, 'ns2:Telephone')
                phone2 = self.get_param(b, 'ns2:Telephone2')
                email = self.get_param(b, 'ns2:EMail')
                client = AvantioBookingClient(name, surname, dni, address, locality, postcode, city, country, country_code, phone, phone2, email)

                #start_date = self.get_param(b, 'ns2:StartDate')
                #end_date = self.get_param(b, 'ns2:EndDate')
                start_time = self.get_param(b, 'ns2:CheckInSchedule')
                end_time = self.get_param(b, 'ns2:CheckOutSchedule')
                start_date = self.get_param(b, 'ns2:ArrivalDate')
                end_date = self.get_param(b, 'ns2:DepartureDate')
                booking_date = self.get_param(b, 'ns2:BookingDate')
                booking_code = self.get_param(b, 'ns2:BookingCode')
                localizator = self.get_param(b, 'ns2:Localizator')
                accommodation_code = self.get_param(b, 'ns2:AccommodationCode')
                user_code = self.get_param(b, 'ns2:UserCode')
                ab = AvantioBooking(start_time,end_time,start_date,end_date,booking_date,booking_code,localizator,accommodation_code,user_code,client)
                booking_list.append(ab)

            if start_date != "":
                self.credentials.pop("StartDate", None)
            if end_date != "":
                self.credentials.pop("EndDate", None)
        return booking_list

    def get_booking(self, code, localizator):
        booking = None
        with self.client.settings(raw_response=True):
            params = self.credentials
            #params['BookingCode'] = code
            #params['Localizator'] = localizator
            params['Localizer'] = code
            resp = self.client.service.GetBooking(**params)
            #b = BeautifulSoup(resp.content, 'xml')
            b = BeautifulSoup(resp.content.decode("utf-8"), 'xml')

            name = self.get_param(b, 'ns2:Name')
            surname = self.get_param(b, 'ns2:Surname')
            dni = self.get_param(b, 'ns2:DNI')
            address = self.get_param(b, 'ns2:Address')
            locality = self.get_param(b, 'ns2:Locality')
            postcode = self.get_param(b, 'ns2:PostCode')
            city = self.get_param(b, 'ns2:City')
            country = self.get_param(b, 'ns2:Country')
            country_code = self.get_param(b, 'ns2:ISOCountryCode')
            phone = self.get_param(b, 'ns2:Telephone')
            phone2 = self.get_param(b, 'ns2:Telephone2')
            email = self.get_param(b, 'ns2:EMail')
            client = AvantioBookingClient(name, surname, dni, address, locality, postcode, city, country, country_code, phone, phone2, email)

            #start_date = self.get_param(b, 'ns2:StartDate')
            #end_date = self.get_param(b, 'ns2:EndDate')
            start_time = self.get_param(b, 'ns2:CheckInSchedule')
            if start_time == "":
                start_time = "00:01"
            end_time = self.get_param(b, 'ns2:CheckOutSchedule')
            if end_time == "":
                end_time = "00:01"
            start_date = self.get_param(b, 'ns2:ArrivalDate')
            end_date = self.get_param(b, 'ns2:DepartureDate')
            booking_date = self.get_param(b, 'ns2:BookingDate')
            booking_code = self.get_param(b, 'ns2:BookingCode')
            localizator = self.get_param(b, 'ns2:Localizator')
            accommodation_code = self.get_param(b, 'ns2:AccommodationCode')
            user_code = self.get_param(b, 'ns2:UserCode')
            booking=AvantioBooking(start_time,end_time,start_date,end_date,booking_date,booking_code,localizator,accommodation_code,user_code,client)
        return booking


    def get_booking_notifications(self):
        booking_list = []
        resp = ""
        with self.client.settings(raw_response=True):
            resp = self.client.service.GetBookingNotifications(**self.credentials)
            #soup = BeautifulSoup(resp.content, 'xml')
            soup = BeautifulSoup(resp.content.decode("utf-8"), 'xml')
            for b in soup.find_all('ns2:Localizer'):
                booking_code = self.get_param(b, 'ns2:BookingCode')
                localizator = self.get_param(b, 'ns2:Localizator')
                an = AvantioNotification(booking_code, localizator)
                booking_list.append(an)
        return booking_list

    def send_pwa_link(self, code, link):
        resp = ""
        with self.client.settings(raw_response=True):
            req = self.credentials
            req["Localizer"] = {"BookingCode": code.split("|")[1], "Localizator": code.split("|")[0]} 
            req["WebAppURL"] = link
            resp = self.client.service.SetSmartLock(**req)
        return resp

'''
    FUNCTIONS
'''
def get_date(date, time, default):
    if date != "" and time != "":
        return datetime.strptime("{} {}".format(date, time), "%Y-%m-%d %H:%M")
    return default + timedelta(days=-1)

def get_dates_range(pau):
    if pau.days > 0:
        start_date = datetime.today()
        end_date = start_date + timedelta(days=pau.days)
    else:
        end_date = datetime.today()
        start_date = end_date + timedelta(days=pau.days)
    return start_date, end_date

def get_dates_range_new(pau):
    if pau.days_new > 0:
        start_date = datetime.today()
        end_date = start_date + timedelta(days=pau.days_new)
    else:
        end_date = datetime.today()
        start_date = end_date + timedelta(days=pau.days_new)
    return start_date, end_date

def get_booking_list(project_uuid):
    err = ""
    booking_list = []
    pau = ProjectAvantioUser.objects.filter(project_uuid=project_uuid).first()
    if pau != None:
        start_date, end_date = get_dates_range(pau)
        start_date_new, end_date_new = get_dates_range_new(pau)

        av = ShAvantio(pau.username, pau.password)
        booking_list = av.get_booking_list(start_date, end_date)
        for booking in booking_list:
            if booking.client.name != "" and booking.client.surname != "":
                checkin = get_date(booking.start_date, booking.start_time, start_date)
                if checkin >= start_date_new and checkin <= end_date_new:
                    code = "{}|{}".format(booking.localizator, booking.booking_code)

                    guest = Guest.objects.filter(ext_id=code, project_id=pau.project_uuid, deleted=0).first()
                    if guest == None:
                        guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=code, project_id=pau.project_uuid)
                        guest.name = booking.client.name
                        guest.surname = booking.client.surname
                        #guest.language = booking.client.languaje
                        guest.mobile = booking.client.phone
                        guest.email = booking.client.email
                        guest.check_in = checkin
                        guest.check_out = get_date(booking.end_date, booking.end_time, start_date)
                        guest.room = booking.accommodation_code
                        guest.save()
                        err = guest.add_all_key_code(code[-4:])
                        av.send_pwa_link(guest.ext_id, guest.pwa_link)
                        booking.created = True
    return booking_list, err

def get_booking_notif(project_uuid):
    pau = ProjectAvantioUser.objects.filter(project_uuid=project_uuid).first()
    booking_list = ""
    if pau != None:
        start_date, end_date = get_dates_range(pau)
        start_date_new, end_date_new = get_dates_range_new(pau)
        av = ShAvantio(pau.username, pau.password)
        booking_list = av.get_booking_notifications()
        for booking in booking_list:
            b = av.get_booking(booking.booking_code, booking.localizator)
            if b != None and b.client.name != "" and b.client.surname != "":
                checkin = get_date(b.start_date, b.start_time, start_date)
                if checkin >= start_date_new and checkin <= end_date_new:
                    code = "{}|{}".format(b.localizator, b.booking_code)
                    guest = Guest.objects.filter(ext_id=code, project_id=pau.project_uuid, deleted=0).first()
                    if guest == None:
                        guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=code, project_id=pau.project_uuid)
                        b.created = True

                    guest.name = b.client.name
                    guest.surname = b.client.surname
                    guest.mobile = b.client.phone
                    guest.email = b.client.email
                    guest.check_in = checkin
                    guest.check_out = get_date(b.end_date, b.end_time, start_date)
                    guest.room = b.accommodation_code
                    guest.save()

                    if b.created:
                        err = guest.add_all_key_code(code[-4:])
                        av.send_pwa_link(guest.ext_id, guest.pwa_link)
    return booking_list

def send_link(project_uuid, guest_uuid):
    resp = "---"
    pau = ProjectAvantioUser.objects.filter(project_uuid=project_uuid).first()
    if pau != None:
        guest = get_or_none(Guest, guest_uuid, "UUID")
        if guest != None:
            av = ShAvantio(pau.username, pau.password)
            resp = av.send_pwa_link(guest.ext_id, guest.pwa_link)
    return resp

