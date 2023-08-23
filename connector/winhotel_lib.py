from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport
#from zeep.settings import Settings
from bs4 import BeautifulSoup

#WSDL = 'http://QUERYAPI2.WINHOTELWEB.COM/query/PublicQuery/hotelsettingquery'
WSDL = 'http://QUERYAPI2.WINHOTELWEB.COM'


class ShWinhotel:
    def __init__(self, username, password):
        self.credentials = {"Credentials": {"UserName": username, "Password": password}}
        #self.settings = Settings(strict=False, xml_huge_tree=True, xsd_ignore_sequence_order=True)
        self.client = Client(WSDL, transport=Transport(session=Session()))

    def get_param(self, b, param):
        try:
            return b.find(param).text
        except Exception as e:
            print(e)
            return ""

    def get_booking_list(self):
        booking_list = []
        with self.client.settings(raw_response=True):
            resp = self.client.service.GetBookingList(**self.credentials)
            print(resp)
#            soup = BeautifulSoup(resp.content, 'xml')
#            for b in soup.find_all('ns2:Booking'):
#                name = self.get_param(b, 'ns2:Name')
#                surname = self.get_param(b, 'ns2:Surname')
#                dni = self.get_param(b, 'ns2:DNI')
#                address = self.get_param(b, 'ns2:Address')
#                locality = self.get_param(b, 'ns2:Locality')
#                postcode = self.get_param(b, 'ns2:PostCode')
#                city = self.get_param(b, 'ns2:City')
#                country = self.get_param(b, 'ns2:Country')
#                country_code = self.get_param(b, 'ns2:ISOCountryCode')
#                phone = self.get_param(b, 'ns2:Telephone')
#                phone2 = self.get_param(b, 'ns2:Telephone2')
#                email = self.get_param(b, 'ns2:EMail')
#                client = AvantioBookingClient(name, surname, dni, address, locality, postcode, city, country, country_code, phone, phone2, email)
#
#                start_date = self.get_param(b, 'ns2:StartDate')
#                end_date = self.get_param(b, 'ns2:EndDate')
#                booking_date = self.get_param(b, 'ns2:BookingDate')
#                booking_code = self.get_param(b, 'ns2:BookingCode')
#                localizator = self.get_param(b, 'ns2:Localizator')
#                accommodation_code = self.get_param(b, 'ns2:AccommodationCode')
#                user_code = self.get_param(b, 'ns2:UserCode')
#                ab = AvantioBooking(start_date, end_date, booking_date, booking_code, localizator, accommodation_code, user_code, client)
#                booking_list.append(ab)
        return booking_list


