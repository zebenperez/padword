import requests
import hashlib
import urllib
import json

API_URL = "http://queryapi2.winhotelweb.com/"
BOOKINGS_URL = "query/PublicQuery/BookingListQuery"

USER = "PADWORD"
PASSWORD = "Pdwrd-z123"
USER_ID = "f6806784-68ba-4930-b26e-194fb5b9aa36"

def get_param(dic, key):
    return dic[key] if key in dic else ""

class WinhotelBooking():
    def __init__(self, dic):
        self.id = get_param(dic, "Id")
        self.code= get_param(dic, "Code")
        self.booking_state = get_param(dic, "BookingState")
        self.stay_state = get_param(dic, "StayState")
        self.check_state = get_param(dic, "CheckState")
        self.check_state_date = get_param(dic, "CheckStateDate")
        self.start_date = get_param(dic, "StartDate")
        self.end_date = get_param(dic, "EndDate")
        self.check_in_date = get_param(dic, "CheckInDate")
        self.check_out_date = get_param(dic, "CheckOutDate")
        self.board_type = get_param(dic, "BoardType")
        self.room_code = get_param(dic, "RoomCode")
        self.allotment_code = get_param(dic, "AllotmentCode")

        pcodes = get_param(dic, "PartnerCodes")
        self.partner_codes = {
            "partner_code1": get_param(pcodes, "PartnerCode1"), 
            "partner_code2": get_param(pcodes, "PartnerCode2"), 
            "partner_code3": get_param(pcodes, "PartnerCode3"), 
            "partner_code4": get_param(pcodes, "PartnerCode4"), 
            "partner_code5": get_param(pcodes, "PartnerCode5"), 
            "partner_code6": get_param(pcodes, "PartnerCode6")
        }

        booker = get_param(dic, "Booker")
        self.booker = {"code": get_param(booker, "Code"), "name": get_param(booker, "Name")}

        room_type = get_param(dic, "RoomType")
        self.room_type = {"code": get_param(room_type, "Code"), "name": get_param(room_type, "Name")}

        room_card = get_param(dic, "RoomCard")
        self.room_card = {"card_id": get_param(booker, "CardID")}

        rate_types = get_param(dic, "RateTypes")
        self.rate_types = []
        for rate in rate_types:
            self.rate_types.append({"code": get_param(rate, "Code"), "name": get_param(rate, "Name")})

        localizers = get_param(dic, "Localizers")
        self.localizers = []
        for loc in localizers:
            self.localizers.append({"localizer_type": get_param(loc, "LocalizerType"), "code": get_param(loc, "Code")})

        occupations = get_param(dic, "Occupations")
        self.occupations = []
        for occ in occupations:
            item = {}
            gt = get_param(occ, "GuestType")
            item["guest_type"] = {"code": get_param(gt, "Code"), "name": get_param(gt, "Name")}
            bt = get_param(occ, "BoarType")
            item["boar_type"] = {"code": get_param(bt, "Code"), "name": get_param(bt, "Name")}
            btr = get_param(occ, "BoarTypeReal")
            item["boar_type_real"] = {"code": get_param(btr, "Code"), "name": get_param(btr, "Name")}
            item["quantity"] = get_param(occ, "Quantity")
            self.occupations.append(item)

        booking_charges = get_param(dic, "BookingCharges")
        self.booking_charges  = []
        for bc in booking_charges:
            item = {}
            item["product_code"] = get_param(bc, "ProductCode")
            item["description"] = get_param(bc, "Description")
            item["quantity"] = get_param(bc, "Quantity")
            item["date"] = get_param(bc, "Date")
            item["start_date"] = get_param(bc, "StartDate")
            item["end_date"] = get_param(bc, "EndDate")
            price = get_param(bc, "Price")
            item["price"] = {"value": get_param(price, "Value"), "currency_code": get_param(price, "CurrencyCode")}
            self.occupations.append(item)

        remarks = get_param(dic, "Remarks")
        self.remarks  = []
        for remark in remarks:
            self.remarks.append(remark)


class WinhotelAPIError(Exception):
    def __init__(self, message='Invalid Parameter'):
        self.message=message

    def __str__(self):
        return 'Error: {}'.format(self.message)

class Winhotel:
    def __init__(self, source_code, target_code):
        self.user = USER
        self.password = PASSWORD
        self.user_id = USER_ID
        self.source_code = source_code
        self.target_code = target_code
 
    def __send_request__(self, _url_request, _json_datas):
        try:
            #_headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Token': '43bedb65e2fa3a57dd19650c7f67a1cb648644f8'}
            _headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
            _response = requests.post(_url_request, headers=_headers, data=_json_datas)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise WinhotelAPIError(message=errh)
        except requests.exceptions.ConnectionError as errc:
            raise WinhotelAPIError(message=errc)
        except requests.exceptions.Timeout as errt:
            raise WinhotelAPIError(message=errt)
        except requests.exceptions.RequestException as err:
            raise WinhotelAPIError(message=err)

    def _credentials(self):
        return {
            "User": self.user,
            "Password": self.password,
            "UserPasswordToken": ""
        }

    def _request_bookings(self):
        json = {}
        request = { 
            "QueryHeader": {
                "HotelCodeMap": {
                    "HotelSourceCode": self.source_code,
                    "HotelTargetCode": self.target_code,
                },
                "MaxRowsResponse": 1
            },
            "BookingListQueryParameters": {
                "StartDateQueryParameter": {
                    "QueryOperator": 0,
                    "Value": "2023-09-01"
                }
            },
        }
        json["QueryCredentials"] = self._credentials()
        json["QueryRequest"] = request
        json["UserID"] = self.user_id
        return json

    def get_bookings(self):
        try:
            _url_request = "{}{}".format(API_URL, BOOKINGS_URL)
            _json = self._request_bookings()
            _json_data = json.dumps(_json)
            return self.__send_request__(_url_request, _json_data).json()["Bookings"]
        except Exception as err:
            raise WinhotelAPIError(message=err)

'''
    FUNCTIONS
'''
def get_booking_list(pau):
    w = Winhotel(pau.source_code, pau.target_code)
    result = w.get_bookings()
    #print(result)
    booking_list = []
    for item in result:
        node = WinhotelBooking(item)
        booking_list.append(node)
    return booking_list


