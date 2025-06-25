from django.conf import settings
from datetime import datetime, timedelta
from web.models import Room
from guest.models import Guest
from padword.commons import new_ui_slug

import requests, json


try:
    API_URL = settings.PAYTEF_API_URL
    CLOUD_URL = settings.PAYTEF_CLOUD_URL
except:
    API_URL = "https://api.paytef.es/json/api/"
    CLOUD_URL = "https://cloud.api.paytef.es/"

TRANSACTION_URL = "transactionConsultation"
TRANSACTION_START_URL = "transaction/start"
TRANSACTION_POLL_URL = "transaction/poll"
PINPAD_STATUS_URL = "pinpad/status"
GET_TOKEN_URL = "authorize"
CONFIG_URL = "configurationConsultation"


def get_param(dic, key):
    return dic[key] if key in dic else ""

class PaytefAPIError(Exception):
    def __init__(self, menssage='Invalid Parameter'):
        self.menssage=menssage

    def __str__(self):
        return 'Error: {}'.format(self.menssage)

class Paytef():
    def __init__(self, username, password, comp, accessKey, secretKey):
        self.username = username 
        self.password = password
        self.company = comp
        self.accessKey = accessKey
        self.secretKey = secretKey
        self.token = ""
    
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
            raise PaytefAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise PaytefAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise PaytefAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise PaytefAPIError(menssage=err)

    def __send_post_request__(self, _url_request, _json):
        try:
            _headers = {}
            #_headers['Accept'] = 'application/json'
            #_headers['x-api-key'] = '{}'.format(self.token)
            _response = requests.post(_url_request, headers=_headers, json=_json)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise PaytefAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise PaytefAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise PaytefAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise PaytefAPIError(menssage=err)

    def __send_post_token_request__(self, _url_request, _json):
        try:
            _headers = {}
            _headers['Authorization'] = f"Bearer {self.token}"
            _headers['Content-Type'] = 'application/json'
            #print("URL: {}".format(_url_request))
            #print("HEADERS: {}".format(_headers))
            #print("PARAM: {}".format(_json))
            _response = requests.post(_url_request, headers=_headers, json=_json, allow_redirects=True)
            #print(_response.text)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise PaytefAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise PaytefAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise PaytefAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise PaytefAPIError(menssage=err)

#    def __send_put_request__(self, _url_request, _json):
#        try:
#            _headers = {}
#            _headers['Authorization'] = 'Bearer {}'.format(self.token)
#            _headers['Content-Type'] = 'application/x-www-form-urlencoded'
#            _response = requests.put(_url_request, headers=_headers, data=_json)
#            _response.raise_for_status()
#            return _response
#        except requests.exceptions.HTTPError as errh:
#            raise PaytefAPIError(menssage=errh)
#        except requests.exceptions.ConnectionError as errc:
#            raise PaytefAPIError(menssage=errc)
#        except requests.exceptions.Timeout as errt:
#            raise PaytefAPIError(menssage=errt)
#        except requests.exceptions.RequestException as err:
#            raise PaytefAPIError(menssage=err)


    def config_query(self):
        try:
            _url_request = "{}{}".format(API_URL, CONFIG_URL)
            params = {
                "authentication": {
                    "username": self.username,
                    "password": self.password,
                    "company": self.company
                },
                "parameters": {
                    #"filterBranch": 0,
                    "detailTerminals": True,
                    "detailDevices": True
                }
            }
            dic = self.__send_post_request__(_url_request, params).json()
            return dic
            #items = dic["data"]
            #return items
        except Exception as err:
            raise PaytefAPIError(menssage=err)

    def transaction_query(self):
        try:
            _url_request = "{}{}".format(API_URL, TRANSACTION_URL)
            params = {
                "authentication": {
                    "username": self.username,
                    "password": self.password,
                    "company": self.company
                },
                "parameters": {
                    "page": "0",
                    "branch": "0",
                    "fromDate": {
                        "year": "2025",
                        "month": "6",
                        "day": "20"
                    },
                    "toDate": {
                        "year": "2025",
                        "month": "6",
                        "day": "21"
                    },
                    "reference": "string",
                    "fromAmount": "12.24",
                    "toAmount": "50",
                    "tcod": "19JQV5",
                    "transactionID": "0",
                    "useLocalTime": "false"
                }
            }
            dic = self.__send_post_request__(_url_request, params).json()
            print(dic)
            return(dic)
            #items = dic["data"]
            #return items
        except Exception as err:
            raise PaytefAPIError(menssage=err)

    def transaction_start_query(self, amount, ref):
        try:
            _url_request = "{}{}".format(API_URL, TRANSACTION_START_URL)
            params = {
                "authentication": {
                    "username": self.username,
                    "password": self.password,
                    "company": self.company
                },
                "parameters": {
                    "cardNumberHashDomain": "branch",
                    #"commerceCodeID": null,
                    "executeOptions": {
                        "method": "polling"
                        #"userData": "null"
                    },
                    "opType": "sale",
                    "pinpad": "*",
                    "requestedAmount": amount,
                    #"requireConfirmation": false,
                    #"tcod": null,
                    "transactionReference": ref
                }
            }
            dic = self.__send_post_request__(_url_request, params).json()
            print(dic)
            return dic
            #items = dic["data"]
            #return items
        except Exception as err:
            raise PaytefAPIError(menssage=err)

    def transaction_poll_query(self, session, ref):
        try:
            _url_request = "{}{}".format(API_URL, TRANSACTION_START_URL)
            params = {
                "authentication": {
                    "username": self.username,
                    "password": self.password,
                    "company": self.company
                },
                "parameters": {
                    "confirmation": "null",
                    "info": {
                        "cardStatus": "waitingForCard",
                        "opType": "sale",
                        "requestedAmount": 0,
                        "sessionID": session,
                        "tcod": "",
                        "transactionConfirmed": "null",
                        "transactionReference": ref,
                        "transactionStatus": "starting"
                    },
                    "result": "null",
                    "resultWorldCoo": "null",
                    "version": "2023.02.040333"
                }
            }
            dic = self.__send_post_request__(_url_request, params).json()
            print(dic)
            return dic
            #items = dic["data"]
            #return items
        except Exception as err:
            raise PaytefAPIError(menssage=err)

    def pinpad_status(self):
        try:
            #_url_request = "{}{}".format(API_URL, PINPAD_STATUS_URL)
            _url_request = "{}{}".format(CLOUD_URL, PINPAD_STATUS_URL)
            #print("--> GET STATUS")
            params = {
                "language": "es",
                "pinpad": "1234"
            }
            dic = self.__send_post_token_request__(_url_request, params).json()
            print(dic)
            return dic
            #items = dic["data"]
            #return items
        except Exception as err:
            raise PaytefAPIError(menssage=err)

    def get_token(self):
        try:
            _url_request = "{}{}".format(CLOUD_URL, GET_TOKEN_URL)
            params = {
                "accessKey": self.accessKey,
                "secretKey": self.secretKey                   
            }
            dic = self.__send_post_request__(_url_request, params).json()
            return dic["result"]["token"]
        except Exception as err:
            raise PaytefAPIError(menssage=err)


#class PaytefBooking():
#    def __init__(self, dic):
#        self.id = get_param(dic, "reservationID")
#        self.property_id = get_param(dic, "propertyID")
#        self.source_id = get_param(dic, "sourceID")
#        self.source_name = get_param(dic, "sourceName")
#        self.guest_id = get_param(dic, "guestID")
#        self.guest_name = get_param(dic, "guestName")
#        self.start = get_param(dic, "startDate")
#        self.end = get_param(dic, "endDate")
#        self.created = get_param(dic, "dateCreated")
#        self.updated = get_param(dic, "dateModified")
#        self.status = get_param(dic, "status")
#        self.adults = get_param(dic, "adults")
#        self.children = get_param(dic, "children")
#        self.balance = get_param(dic, "balance")
#        #self.customer = None
#        self.rooms = []
#        self.created = False

'''
    FUNCTIONS
'''
def get_config(ppu):
    pt = Paytef(ppu.username, ppu.password, ppu.company, "", "")
    res = pt.config_query()
    print(res)
    return res
    #pt.transaction_query()
 
#def trans_start(ppu):
#    pt = Paytef(ppu.username, ppu.password, ppu.company)
def trans_start():
    pt = Paytef("7CucWdfBNR8xK8xR6", "7e7cfmMyqm_qCZgNa3", "113202", "", "")
    res = pt.transaction_start_query(10, "Op Test 1")
    print(res)

def get_token():
    pt = Paytef("", "", "", "MS4yZmNp", "9KiyvtmGpVB9RHbLWvq4A494MwKbu2lfA5Zixdov")
    pt.token = pt.get_token()
    print(pt.token)

def get_status():
    pt = Paytef("", "", "", "MS4yZmNp", "9KiyvtmGpVB9RHbLWvq4A494MwKbu2lfA5Zixdov")
    #pt.token = pt.get_token()
    pt.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcHlJZCI6MTEzMjAyLCJpYXQiOjE3NTA4NDc3MDUsImV4cCI6MTc1MDkzNDEwNSwiYXVkIjoidXJuOnBheXRlZjpkZXZpY2UtYXBpLWNsb3VkIiwiaXNzIjoidXJuOnBheXRlZjphd3MifQ.fBoFEaaKYldZYfpbkgY7Qui6BwAOh8lI1VQP-Vodg18"
    #print("TOKEN: {}".format(pt.token))
    res = pt.pinpad_status()
    print(res)
