from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
#from zeep.settings import Settings
from bs4 import BeautifulSoup

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
    def __init__(self, start_date, end_date, booking_date, booking_code, localizator, accommodation_code, user_code, client):
        self.start_date = start_date
        self.end_date = end_date
        self.booking_date = booking_date
        self.booking_code = booking_code
        self.localizator = localizator
        self.accommodation_code = accommodation_code
        self.user_code = user_code
        self.client = client
    
class ShAvantio:
    def __init__(self):
        self.credentials = {"Credentials": {"UserName": "GA5db1150035", "Password": "efd4ec0bf530"}}
        #self.settings = Settings(strict=False, xml_huge_tree=True, xsd_ignore_sequence_order=True)
        self.client = Client(WSDL, transport=Transport(session=Session()))

    def get_booking_list(self):
        booking_list = []
        with self.client.settings(raw_response=True):
            resp = self.client.service.GetBookingList(**self.credentials)
            soup = BeautifulSoup(resp.content, 'xml')
            for b in soup.find_all('ns2:Booking'):
                name = b.find('ns2:Name').text
                surname = b.find('ns2:Surname').text
                dni = b.find('ns2:DNI').text
                address = b.find('ns2:Address').text
                locality = b.find('ns2:Locality').text
                postcode = b.find('ns2:PostCode').text
                city = b.find('ns2:City').text
                country = b.find('ns2:Country').text
                country_code = b.find('ns2:ISOCountryCode').text
                phone = b.find('ns2:Telephone').text
                phone2 = b.find('ns2:Telephone2').text
                email = b.find('ns2:EMail').text
                client = AvantioBookingClient(name, surname, dni, address, locality, postcode, city, country, country_code, phone, phone2, email)

                start_date = b.find('ns2:StartDate').text
                end_date = b.find('ns2:EndDate').text
                booking_date = b.find('ns2:BookingDate').text
                booking_code = b.find('ns2:BookingCode').text
                localizator = b.find('ns2:Localizator').text
                accommodation_code = b.find('ns2:AccommodationCode').text
                user_code = b.find('ns2:UserCode').text
                ab = AvantioBooking(start_date, end_date, booking_date, booking_code, localizator, accommodation_code, user_code, client)
                print(ab)
                booking_list.append(ab)
        return booking_list

