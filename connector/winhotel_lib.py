from django.conf import settings
from datetime import datetime, timedelta
from django.db.models import Count

from bookings.models import Form, FormType
from contents.models import ItemInCat, Category, Item, ItemPrice, PointOfSale, PointOfSaleCategory, PosCodeItem
from guest.models import Guest, Regime, GuestRegime, ProjectRegime
from web.models import Room
from padword.commons import new_ui_slug

import requests
import hashlib
import urllib
import json
import random
import os

API_URL = "http://queryapi2.winhotelweb.com/"
BOOKINGS_URL = "query/PublicQuery/BookingListQuery"
SEND_CHARGE_URL = "query/PublicQuery/ExternalChargeInsert"

USER = "PADWORD"
PASSWORD = "Pdwrd-z123"
USER_ID = "f6806784-68ba-4930-b26e-194fb5b9aa36"

def get_param(dic, key):
    return dic[key] if key in dic else ""

def write_log(result):
    f = open(os.path.join(settings.BASE_DIR, "winhotel.log"), "a", encoding='utf-8')
    f.write("{}\n".format(result))
    f.close()

class WinhotelGuest():
    def __init__(self, dic):
        self.code = get_param(dic, "Code")
        self.name = get_param(dic, "Name")
        
        contact = get_param(dic, "Contact")
        self.contact = {
            "code": get_param(contact, "Code"), 
            "fidelity_code": get_param(contact, "FidelityCode"),
            "contact_name": get_param(contact, "ContactName"),
            "name": get_param(contact, "Name"), 
            "surname": get_param(contact, "SurName"), 
            "second_surname": get_param(contact, "SecondSurName"), 
            "father_name": get_param(contact, "FatherName"), 
            "mother_name": get_param(contact, "MotherName"), 
            "title": get_param(contact, "Title"), 
            "gender": get_param(contact, "Gender"), 
            "birth_date": get_param(contact, "BirthDate"), 
            "financials_society": get_param(contact, "FinancialsSociety"), 
            "preference": get_param(contact, "preference"), 
            "repeat_guest": get_param(contact, "RepeatGuest"), 
            "data_validated": get_param(contact, "DataValidated"), 
            "id": get_param(contact, "Id"), 
        }

        nat = get_param(contact, "Nationality")
        self.contact["nationality"] = {"code": get_param(nat, "Code"), "name": get_param(nat, "Name"), "code_iso":  get_param(nat, "CodeISO")}

        addresses = get_param(contact, "Addresses")
        self.contact["addresses"] = []
        for add in addresses:
            a = {
                "address_line1": get_param(add, "AddressLine1"), 
                "address_line2": get_param(add, "AddressLine2"), 
                "post_code": get_param(add, "PostCode"), 
                "city": get_param(add, "City"), 
                "state": get_param(add, "State"), 
                "address_type": get_param(add, "AddressType")
            }
            country = get_param(add, "Country")
            a["country"] = {"code": get_param(country, "Code"), "name": get_param(country, "Name")}
            self.contact["addresses"].append(a)

        phones = get_param(contact, "Phones")
        self.contact["phones"] = []
        for ph in phones:
            p = { "phone_type":get_param(add,"PhoneType"),"phone_area":get_param(add,"PhoneArea"),"phone_number":get_param(add,"PhoneNumber"), }
            self.contact["phones"].append(p)

        language = get_param(contact, "Language")
        self.contact["language"] = {"code": get_param(language, "Code"), "name": get_param(language, "Name")}
        
        emails = get_param(contact, "EMails")
        self.contact["emails"] = []
        for email in emails:
            self.contact["emails"].append(email)

        identity_documents = get_param(contact, "IdentityDocuments")
        self.contact["identity_documents"] = []
        for doc in identity_documents:
            d = { 
                "identity_type": get_param(doc, "IdentityType"),
                "number_id": get_param(doc, "NumberID"),
                "birth_date": get_param(doc, "BirthDate"), 
                "expedition_date": get_param(doc, "ExpeditionDate"), 
                "expiration_date": get_param(doc, "ExpirationDate"), 
            }
            nationality = get_param(doc, "Nationality")
            d["nationality"] = {"code":get_param(nationality,"Code"),"name":get_param(nationality,"Name"),"code_iso":get_param(nationality,"CodeISO")}
            self.contact["identity_documents"].append(d)

        remarks = get_param(contact, "Remarks")
        self.contact["remarks"] = []
        for remark in remarks:
            self.contact["remarks"].append(remark)

 
class WinhotelBooking():
    def __init__(self, dic):
        self.created = False
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

        guests = get_param(dic, "Guests")
        self.guests = []
        for guest in guests:
            g = WinhotelGuest(guest)
            self.guests.append(g)


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

    def _request_header(self):
        return {
            "HotelCodeMap": {
                "HotelSourceCode": self.source_code,
                "HotelTargetCode": self.target_code,
            },
            "MaxRowsResponse": 1
        }

    def _request_bookings(self, state):
        json = {"QueryCredentials": self._credentials(), "UserID": self.user_id}
        _bookings_params = {
            "BookingStateQueryParameters": [{
                "QueryOperator": 0,
                "Value": state
            }]
        }
        json["QueryRequest"] = {"QueryHeader": self._request_header(), "BookingListQueryParameters": _bookings_params}
        return json

    def _request_bookings_new(self, state, start_date, end_date, date_operator=1):
        json = {"QueryCredentials": self._credentials(), "UserID": self.user_id}
        _bookings_params = {
            "StartDateQueryParameter": {
                "QueryOperator": date_operator,
                "Value": start_date
            },
            "BookingStateQueryParameters": [{
                "QueryOperator": 0,
                "Value": state
            }],
        }
        json["QueryRequest"] = {"QueryHeader": self._request_header(), "BookingListQueryParameters": _bookings_params}
        return json

    def _request_bookings_day(self, state, date):
        json = {"QueryCredentials": self._credentials(), "UserID": self.user_id}
        _bookings_params = {
            "StartDateQueryParameter": {
                "QueryOperator": 0,
                "Value": date
            },
            "BookingStateQueryParameters": [{
                "QueryOperator": 0,
                "Value": state
            }],
        }
        json["QueryRequest"] = {"QueryHeader": self._request_header(), "BookingListQueryParameters": _bookings_params}
        return json

    def _request_bookings_range(self, state, ini_date, end_date):
        json = {"QueryCredentials": self._credentials(), "UserID": self.user_id}
        _bookings_params = {
            "StartDateFromToQueryParameter": {
                "From": ini_date,
                "To": end_date
            },
            "BookingStateQueryParameters": [{
                "QueryOperator": 0,
                "Value": state
            }],
        }
        json["QueryRequest"] = {"QueryHeader": self._request_header(), "BookingListQueryParameters": _bookings_params}
        return json

    def _request_send_charge(self, dic):
        json = {"QueryCredentials": self._credentials(), "UserID": self.user_id}
        _send_charge_params = {
            "ExternalCharge": {
                "BookingCode": dic["BookingCode"],
                "CreditContact": {
                    "RoomCode": dic["CreditContact"]["RoomCode"],
                    "ContactName": dic["CreditContact"]["ContactName"],
                    "ContactId": dic["CreditContact"]["ContactId"],
                    "HasCredit": dic["CreditContact"]["HasCredit"],
                    "LimitCredit": dic["CreditContact"]["LimitCredit"]
                },
                "Source": dic["Source"],
                "SourceDocument": dic["SourceDocument"],
                "Date": dic["Date"],
                "TotalAmount": dic["TotalAmount"],
                "CashCode": dic["CashCode"]
            }
        }
        json["QueryRequest"] = {"QueryHeader": self._request_header(), "InsertExternalChargeRequest": _send_charge_params}
        return json

    def _request_send_liq(self, dic):
        json = {"QueryCredentials": self._credentials(), "UserID": self.user_id}
        _send_charge_params = {
            "ExternalCharge": {
                "CreditContact": {
                    "RoomCode": "",
                    "ContactName": dic["CreditContact"]["ContactName"],
                    "ContactId": dic["CreditContact"]["ContactId"],
                    "HasCredit": "true",
                },
                "Source": dic["Source"],
                "SourceDocument": dic["SourceDocument"],
                "Date": dic["Date"],
                "TotalAmount": dic["TotalAmount"],
                "CashCode": dic["CashCode"]
            }
        }
        json["QueryRequest"] = {"QueryHeader": self._request_header(), "InsertExternalChargeRequest": _send_charge_params}
        return json


    def get_bookings(self, state):
        try:
            _url_request = "{}{}".format(API_URL, BOOKINGS_URL)
            _json = self._request_bookings(state)
            _json_data = json.dumps(_json)
            return self.__send_request__(_url_request, _json_data).json()["Bookings"]
        except Exception as err:
            raise WinhotelAPIError(message=err)

    def get_bookings_new(self, state, start_date, end_date, date_operator=1):
        try:
            _url_request = "{}{}".format(API_URL, BOOKINGS_URL)
            _json = self._request_bookings_new(state, start_date, end_date, date_operator)
            _json_data = json.dumps(_json)
            return self.__send_request__(_url_request, _json_data).json()["Bookings"]
        except Exception as err:
            raise WinhotelAPIError(message=err)

    def get_bookings_day(self, state, date):
        try:
            _url_request = "{}{}".format(API_URL, BOOKINGS_URL)
            _json = self._request_bookings_day(state, date)
            _json_data = json.dumps(_json)
            return self.__send_request__(_url_request, _json_data).json()["Bookings"]
        except Exception as err:
            raise WinhotelAPIError(message=err)

    def get_bookings_range(self, state, ini_date, end_date):
        try:
            _url_request = "{}{}".format(API_URL, BOOKINGS_URL)
            _json = self._request_bookings_range(state, ini_date, end_date)
            _json_data = json.dumps(_json)
            return self.__send_request__(_url_request, _json_data).json()["Bookings"]
        except Exception as err:
            raise WinhotelAPIError(message=err)

    def send_charge(self, dic):
        try:
            _url_request = "{}{}".format(API_URL, SEND_CHARGE_URL)
            _json = self._request_send_charge(dic)
            _json_data = json.dumps(_json)
            #write_log("--------> WH LIB ENVIO POST")
            write_log(str(_json))
            return self.__send_request__(_url_request, _json_data).json()
        except Exception as err:
            write_log("--------> WH LIB ERROR: {}".format(err))
            raise WinhotelAPIError(message=err)

    def send_liq(self, dic):
        try:
            _url_request = "{}{}".format(API_URL, SEND_CHARGE_URL)
            _json = self._request_send_liq(dic)
            _json_data = json.dumps(_json)
            #write_log("--------> WH LIB ENVIO POST")
            write_log(str(_json))
            return self.__send_request__(_url_request, _json_data).json()
        except Exception as err:
            write_log("--------> WH LIB ERROR: {}".format(err))
            raise WinhotelAPIError(message=err)


'''
    FUNCTIONS
'''
def room_exist(project_uuid, room):
    count = Room.objects.filter(project_uuid=project_uuid, number=room).count()
    return (count > 0)

def get_guest(booking):
    return booking.guests[0] if len(booking.guests) > 0 else None

def get_contact(guest):
    return guest.contacts[0] if len(guest.contacts) > 0 else None

def get_phone(contact):
    return contact["phones"][0] if len(contact["phones"]) > 0 else None

def get_email(contact):
    return contact["emails"][0] if len(contact["emails"]) > 0 else None

def get_checkin(pwu, checkin):
    if pwu.update_checkin:
        return checkin.replace(hour=pwu.ini_time.hour, minute=pwu.ini_time.minute)
    return checkin

def get_checkout(pwu, checkout):
    if pwu.update_checkin:
        return checkout.replace(hour=pwu.end_time.hour, minute=pwu.end_time.minute)
    return checkout

def set_regime(booking, guest):
    try:
        reg_name = booking.occupations[0]["boar_type_real"]["name"]
        reg_code = booking.occupations[0]["boar_type_real"]["code"]
        project = guest.project
        regime = Regime.objects.filter(code=reg_code, project_uuid=project.uuid).first()
        if regime != None:
            gr_list = GuestRegime.objects.filter(guest=guest)
            gr_list.delete()
            GuestRegime.objects.create(regime=regime, guest=guest)        

            pr = ProjectRegime.objects.filter(regime=regime, project=project).first()        
            if pr == None:
                pr = ProjectRegime.objects.create(regime=regime, project=project)        

#        #regime = Regime.objects.filter(code=reg_code).first()
#        regime_list = Regime.objects.filter(code=reg_code)
#        #if regime != None:
#        for regime in regime_list:
#            #Activa si solo este el generico o es un regimen creado a medida para un proyecto
#            if len(regime_list) == 1 or regime.project_uuid != "":
#                gr_list = GuestRegime.objects.filter(guest=guest)
#                gr_list.delete()
#                GuestRegime.objects.create(regime=regime, guest=guest)        
#
#                pr = ProjectRegime.objects.filter(regime=regime, project=guest.project).first()        
#                if pr == None:
#                    pr = ProjectRegime.objects.create(regime=regime, project=guest.project)        
    except Exception as e:
        print(e)
        return ""

def create_booking(pwu, booking):
    checkin = datetime.strptime(booking.check_in_date.split('+')[0], "%Y-%m-%dT%H:%M:%S")
    checkout = datetime.strptime(booking.check_out_date.split('+')[0], "%Y-%m-%dT%H:%M:%S")
    room = booking.room_code 
    room_ex = room_exist(pwu.project_uuid, room)
    if room_ex and checkout >= datetime.now():
        guest = Guest.objects.filter(ext_id=booking.code, project_id=pwu.project_uuid, deleted=0).first()
        if guest == None:
            guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=booking.code, project_id=pwu.project_uuid)
            booking.created = True

        wguest = get_guest(booking)
        if wguest != None:
            guest.name = wguest.contact["name"]
            guest.surname = wguest.contact["surname"]

            phone = get_phone(wguest.contact)
            if phone != None:
                guest.mobile = phone["phone_number"]

            email = get_email(wguest.contact)
            if email != None:
                guest.email = email
            
        #guest.check_in = checkin
        #guest.check_out = checkout
        guest.check_in = get_checkin(pwu, checkin)
        guest.check_out = get_checkout(pwu, checkout)
        guest.room = room
        guest.save()
        set_regime(booking, guest)

def create_booking_new(pwu, booking, start_date, end_date):
    checkin = datetime.strptime(booking.check_in_date.split('+')[0], "%Y-%m-%dT%H:%M:%S")
    checkout = datetime.strptime(booking.check_out_date.split('+')[0], "%Y-%m-%dT%H:%M:%S")
    room = booking.room_code 
    room_ex = room_exist(pwu.project_uuid, room)
    if room_ex and checkin >= start_date and checkin <= end_date:
        guest = Guest.objects.filter(ext_id=booking.code, project_id=pwu.project_uuid, deleted=0).first()
        if guest == None:
            guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=booking.code, project_id=pwu.project_uuid)
            booking.created = True

        wguest = get_guest(booking)
        if wguest != None:
            guest.name = wguest.contact["name"]
            guest.surname = wguest.contact["surname"]
            guest.PID = wguest.contact["id"]

            phone = get_phone(wguest.contact)
            if phone != None:
                guest.mobile = phone["phone_number"]

            email = get_email(wguest.contact)
            if email != None:
                guest.email = email
            
        #guest.check_in = checkin
        #guest.check_out = checkout
        guest.check_in = get_checkin(pwu, checkin)
        guest.check_out = get_checkout(pwu, checkout)
        guest.room = room
        guest.save()
        set_regime(booking, guest)

        if booking.created:
            err = guest.add_all_key_code(random.randint(1000, 9999))
        #    lock_code = get_code(pau, code)
        #    err = guest.add_all_key_code(lock_code)
        #    av.send_pwa_link(guest.ext_id, guest.pwa_link)

def create_booking_day(pwu, booking):
    checkin = datetime.strptime(booking.check_in_date.split('+')[0], "%Y-%m-%dT%H:%M:%S")
    checkout = datetime.strptime(booking.check_out_date.split('+')[0], "%Y-%m-%dT%H:%M:%S")
    room = booking.room_code 
    room_ex = room_exist(pwu.project_uuid, room)
    if room_ex:
        guest = Guest.objects.filter(ext_id=booking.code, project_id=pwu.project_uuid, deleted=0).first()
        if guest == None:
            guest = Guest(UUID = new_ui_slug(Guest, "UUID"), ext_id=booking.code, project_id=pwu.project_uuid)
            booking.created = True

        wguest = get_guest(booking)
        if wguest != None:
            guest.name = wguest.contact["name"]
            guest.surname = wguest.contact["surname"]

            phone = get_phone(wguest.contact)
            if phone != None:
                guest.mobile = phone["phone_number"]

            email = get_email(wguest.contact)
            if email != None:
                guest.email = email
            
        #guest.check_in = checkin
        #guest.check_out = checkout
        guest.check_in = get_checkin(pwu, checkin)
        guest.check_out = get_checkout(pwu, checkout)
        guest.room = room
        guest.save()
        set_regime(booking, guest)

        if booking.created:
            err = guest.add_all_key_code(random.randint(1000, 9999))

def delete_booking(pwu, booking):
    guest = Guest.objects.filter(ext_id=booking.code, project_id=pwu.project_uuid, deleted=0).first()
    if guest == None:
        guest.delete_soft()

#def get_booking_list(pau, start_date, end_date):
def get_booking_list(pwu, state):
    w = Winhotel(pwu.source_code, pwu.target_code)
    result = w.get_bookings(state)
    #result = w.get_bookings(start_date, end_date)
    #print(result)
    booking_list = []
    for item in result:
        node = WinhotelBooking(item)
        booking_list.append(node)
        create_booking(pwu, node)
    return booking_list, ""

def get_booking_new_list(pwu, state):
    today = datetime.today()
    e_date = today + timedelta(pwu.days)
    start_date = today.strftime("%Y-%m-%d")
    end_date = e_date.strftime("%Y-%m-%d") 

    w = Winhotel(pwu.source_code, pwu.target_code)
    result = w.get_bookings_new(state, start_date, end_date, pwu.import_operator)
    booking_list = []
    for item in result:
        node = WinhotelBooking(item)
        booking_list.append(node)
        create_booking_new(pwu, node, today, e_date)
    return booking_list, ""

def get_booking_day_list(pwu, state, source, target, date):
    w = Winhotel(source, target)
    result = w.get_bookings_day(state, date)
    booking_list = []
    for item in result:
        node = WinhotelBooking(item)
        booking_list.append(node)
        create_booking_day(pwu, node)
    return booking_list, ""

def get_booking_range_list(pwu, state):
    today = datetime.today()
    e_date = today + timedelta(pwu.days)
    start_date = today.strftime("%Y-%m-%d")
    end_date = e_date.strftime("%Y-%m-%d") 

    w = Winhotel(pwu.source_code, pwu.target_code)
    result = w.get_bookings_range(state, start_date, end_date)
    booking_list = []
    for item in result:
        node = WinhotelBooking(item)
        booking_list.append(node)
        create_booking_new(pwu, node, today, e_date)
    return booking_list, ""

def get_booking_cancelled(pwu, state):
    w = Winhotel(pwu.source_code, pwu.target_code)
    result = w.get_bookings(state)
    booking_list = []
    for item in result:
        node = WinhotelBooking(item)
        booking_list.append(node)
        delete_booking(pwu, node)
    return booking_list, ""

def send_charge(pwu,booking_code,room_code,contact_name,contact_id,has_credit,limit_credit,source,source_document,date,total_amount,cash_code):
    dic = {
        "BookingCode": booking_code,
        "CreditContact": {
            "RoomCode": room_code,
            "ContactName": contact_name,
            "ContactId": contact_id,
            "HasCredit": has_credit,
            "LimitCredit": limit_credit
        },
        "Source": source,
        "SourceDocument": source_document,
        "Date": date,
        "TotalAmount": total_amount,
        "CashCode": cash_code
    }
    w = Winhotel(pwu.source_code, pwu.target_code)
    #write_log("--------> WH LIB ENVIO")
    result = w.send_charge(dic)
    #write_log("--------> WH LIB ENVIADO")
    write_log(result)

def send_liq(pwu, contact_name, contact_id, source, source_document, date, total_amount, cash_code):
    dic = {
        "CreditContact": {
            "ContactName": contact_name,
            "ContactId": contact_id,
        },
        "Source": source,
        "SourceDocument": source_document,
        "Date": date,
        "TotalAmount": total_amount,
        "CashCode": cash_code
    }
    w = Winhotel(pwu.source_code, pwu.target_code)
    #write_log("--------> WH LIB ENVIO")
    result = w.send_charge(dic)
    #write_log("--------> WH LIB ENVIADO")
    write_log(result)


'''
    Import
'''
def get_tpv_cat(project_uuid):
    form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=project_uuid).first()
    return form.get_category

def get_or_create_item(dic_line, project_uuid, now):
    uuid = new_ui_slug(Item)
    price = float(dic_line[5].replace(",", "."))

    item_list = Item.objects.filter(ext_id=dic_line[3])
    item = None
    for it in item_list:
        if it.project != None and it.project.uuid == project_uuid:
            item = it
            break
    if item == None:
        item = Item.objects.create(uuid=uuid, ext_id=dic_line[3], created_at=now, updated_at=now)
    item.is_active = 1
    item.price = price
    item.name = dic_line[4]
    item.updated_at = now
    item.save()
    return item
 
def create_items(project_uuid, dic_line):
    update = False
    cat_id = dic_line[6].zfill(4)
    now = datetime.now()
    category_list = list(Category.objects.filter(project_uuid=project_uuid, internal=cat_id))

    #Si no existe la categoría se crea de tipo tpv_list
    if len(category_list) == 0:
        cat = get_tpv_cat(project_uuid)
        uuid = new_ui_slug(Category)
        name = json.dumps({"ES": "{}".format(dic_line[7])})
        cat = Category.objects.create(uuid=uuid, project_uuid=project_uuid, is_active=1, updated_at=now, created_at=now, name=name, internal=cat_id, parent=cat)
        category_list.append(cat)

        ft = FormType.objects.filter(project_uuid=project_uuid, code="tpv_list").first()
        form = Form.objects.create(uuid=new_ui_slug(Form), category=cat.uuid, form_type=ft)

    #Se crea el item para todas las categorías con el código indicado
    for cat in category_list:
        #item = Item.objects.create(uuid=uuid, is_active=1, price=price, name=dic_line[4], ext_id=dic_line[3], updated_at=now, created_at=now)
        #item.save()
        item = get_or_create_item(dic_line, project_uuid, now)
        new_position = 0
        if ItemInCat.objects.filter(category=cat).exists():
            new_position = ItemInCat.objects.filter(category = cat).order_by('position').last().position + 1
        ic = ItemInCat(position=new_position, category=cat, item=item)
        ic.save()
        update = True
    return update

def unactive_items(project_uuid, id_list):
    cat = get_tpv_cat(project_uuid)
    ic_list = ItemInCat.objects.filter(category__parent = cat).exclude(item__ext_id__in = id_list)
    for ic in ic_list:
        ic.item.is_active = 0
        ic.item.save()
 
def unactive_categories(project_uuid, cat_list):
    cat = get_tpv_cat(project_uuid)
    #Desactivamos las categorías que no están en el listado
    category_list = Category.objects.filter(project_uuid=project_uuid, parent=cat, is_active=1).exclude(internal__in = cat_list)
    for c in category_list:
        c.is_active = 0
        c.save()
        update_tpv_cat("", c, False)

    #Desactivamos las categorías que tienen todos los items desactivados
    category_list = Category.objects.filter(project_uuid=project_uuid, parent=cat, is_active=1)
    for c in category_list:
        if len(c.get_items_active) == 0:
            c.is_active = 0
            c.save()
            update_tpv_cat("", c, False)

def update_item_pos_price(project_uuid, dic):
    cat_id = dic[6].zfill(4)
    item_id = dic[3]
    pos_code = dic[0]
    regime_code = dic[2]
    price = dic[5].replace(",", ".")
    #print("-- ENTRANDO")
    #print(cat_id)
    #print(item_id)
    #print(pos_code)
    #print(regime_code)
    #print(price)

    pos = PointOfSale.objects.filter(project_uuid=project_uuid, ext_code=pos_code).first()
    #print("POS: {}".format(pos))
    if pos != None:
        regime_list = ProjectRegime.objects.filter(project__uuid=project_uuid, regime__alt_code=regime_code)
        for regime in regime_list:
            #print("REG: {}".format(regime))
            category_list = list(Category.objects.filter(project_uuid=project_uuid, internal=cat_id))
            for cat in category_list:
                #print("CAT: {}".format(cat))
                ic_list = ItemInCat.objects.filter(category=cat, item__ext_id=item_id)
                for ic in ic_list:
                    #print("ITEM: {}".format(ic.item))
                    #ip_list = ItemPrice.objects.filter(item=ic.item, pos=pos.uuid, regime_code=regime.regime.code)
                    #if len(ip_list) > 0:
                    #    for ip in ip_list:
                    #        ip.delete()
                    ItemPrice.objects.filter(item=ic.item, pos=pos.uuid, regime_code=regime.regime.code).delete()
                    ip, created = ItemPrice.objects.get_or_create(item=ic.item, pos=pos.uuid, regime_code=regime.regime.code)
                    ip.price = float(price)
                    ip.save()
                    #print("{} {}({}) {}".format(ip.pos, ip.regime_code, regime.regime.code, ip.price))

def update_tpv_cat(pos_code, cat, active):
    if active:
        pos = PointOfSale.objects.filter(ext_code=pos_code, project_uuid=cat.project_uuid).first()
        if pos != None:
            PointOfSaleCategory.objects.get_or_create(category=cat, point_of_sale=pos)
    else:
        posc_list = PointOfSaleCategory.objects.filter(category=cat)
        for posc in posc_list:
            posc.delete()
        #posc = PointOfSaleCategory.objects.filter(category=cat, point_of_sale=pos).first()
        #if posc != None:
        #    posc.delete()

def update_item_price_default(project_uuid, regime_code, item, price):
    regime_list = ProjectRegime.objects.filter(project__uuid=project_uuid, regime__alt_code=regime_code)
    for regime in regime_list:
#        ip_list = ItemPrice.objects.filter(item=item, pos="", regime_code=regime.regime.code)
#        if len(ip_list) > 0:
#            for ip in ip_list:
#                ip.delete()
        ItemPrice.objects.filter(item=item, pos="", regime_code=regime.regime.code).delete()
        ip, created = ItemPrice.objects.get_or_create(item=item, pos="", regime_code=regime.regime.code)
            
        ip.price = float(price)
        ip.save()

def clean_pos_code_item(project_uuid):
    PosCodeItem.objects.filter(project_uuid=project_uuid).delete()

def clean_price_item(project_uuid):
    form = Form.objects.filter(form_type__code="tpv", form_type__project_uuid=project_uuid).first()
    cat = form.get_category
    cat_list = Category.objects.filter(parent=cat)
    regime_list = ProjectRegime.objects.filter(project__uuid=project_uuid)
    for cat in cat_list:
        item_list = cat.get_items
        for item in item_list:
            item.price = 0
            item.save()
            for reg in regime_list:
                update_item_price_default(project_uuid, reg.regime.code, item, 0)

def set_pos_code_item(dic, project_uuid):
    pos = dic[0]
    code = dic[9]
    name = dic[10]
    item = dic[3]
    pci, created = PosCodeItem.objects.get_or_create(item_id=item, code=code, name=name, pos=pos, project_uuid=project_uuid)

def check_item_cat(project_uuid):
    c_list = Category.objects.filter(project_uuid=project_uuid).values('internal').annotate(total=Count('id')).filter(total__gt=1)
    i_list = Item.objects.values('ext_id').annotate(total=Count('id')).filter(total__gt=1)
    write_log("{} - CATEGORIAS DUPLICADAS:".format(datetime.now()))
    write_log(c_list)
    write_log("{} - ITEMS DUPLICADOS:".format(datetime.now()))
    write_log(i_list)

def import_item_prices(file, project_uuid, update_all_prices=False):
    updated = []
    not_updated = []
    decoded_file = file.read().decode('latin-1').splitlines()
    id_list = []
    cat_list = []
    #print("--> 1")
    #Eliminamod los items con los códigos en los tpv
    clean_price_item(project_uuid)
    clean_pos_code_item(project_uuid)
    for line in decoded_file:
        update = False
        try:
            dic_line = line.split(";")
            ext_id = int(dic_line[3])
            name = dic_line[4]
            price = float(dic_line[5].replace(",", "."))
            cat_id = dic_line[6].zfill(4)
            #print("{} - {}".format(dic_line[3], dic_line[5]))

            #Actualización de los items con los códigos en los tpv
            set_pos_code_item(dic_line, project_uuid)

            id_list.append(ext_id)
            if cat_id not in cat_list:
                cat_list.append(cat_id)

            ic_list = ItemInCat.objects.filter(category__project_uuid = project_uuid, item__ext_id = ext_id)
            if len(ic_list) == 0:
                update = create_items(project_uuid, dic_line)

            for ic in ic_list:
                #Actualizamos el nombre
                if name != ic.item.name:
                    ic.item.name = name
                    ic.item.save()
                    update = True
                #Actualizamos el precio, se selecciona el precio mayor
                #if price != ic.item.price:
                if float(price) > float(ic.item.price):
                    #print("Actualiza precio {}".format(price))
                    ic.item.price = price
                    ic.item.save()
                    update = True
                    update_item_price_default(project_uuid, dic_line[2], ic.item, price)
                #Activamos el item si no lo está
                if ic.item.is_active == 0:
                    ic.item.is_active = 1
                    ic.item.save()
                    update = True
                #Activamos la categoría si no lo está
                if ic.category.is_active == 0:
                    ic.category.is_active = 1
                    ic.category.save()
                    update_tpv_cat(dic_line[0], ic.category, True)
                if update_all_prices:
                    #print("--> 2")
                    update_item_pos_price(project_uuid, dic_line)
                    #for ip in ic.item.prices.all():
                    #    ip.price = price
                    #    ip.save()
        except Exception as e:
            print(line)
            print(e)
        if update:
            updated.append(dic_line)
        else:
            not_updated.append(dic_line)
    unactive_items(project_uuid, id_list)
    unactive_categories(project_uuid, cat_list)
    check_item_cat(project_uuid)
    return updated, not_updated


