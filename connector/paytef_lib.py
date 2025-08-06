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
TRANSACTION_RESULT_URL = "transaction/result"
MIFARE_START_URL = "miFare/read/start"
MIFARE_POLL_URL = "miFare/read/poll"
MIFARE_RESULT_URL = "miFare/read/result"
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
    def __init__(self, username, password, comp, accessKey, secretKey, token=""):
        self.username = username 
        self.password = password
        self.company = comp
        self.accessKey = accessKey
        self.secretKey = secretKey
        self.token = token
    
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
            print(_response.text)
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
            print("-------------------------------------------------------------------------------------")
            print(_response.text)
            if "error" in _response.text:
                return _response

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

    def transaction_start_query(self, ppu, tcod, amount, ref, op_type="sale"):
        try:
            _url_request = "{}{}".format(CLOUD_URL, TRANSACTION_START_URL)
            params = {
                "executeOptions": {
                    "method": "polling"
                },
                "opType": op_type,
                "pinpad": tcod,
                "requestedAmount": amount,
                "transactionReference": ref
            }

            dic = self.__send_post_token_request__(_url_request, params).json()

            if self.update_token(dic, ppu):
                dic = self.__send_post_token_request__(_url_request, params).json()

            #print(dic)
            return dic["info"]["sessionID"]
        except Exception as err:
            raise PaytefAPIError(menssage=err)

    def transaction_poll_query(self, tcod):
        try:
            _url_request = "{}{}".format(CLOUD_URL, TRANSACTION_POLL_URL)
            params = { "pinpad": tcod, }
            dic = self.__send_post_token_request__(_url_request, params).json()
            #print(dic)
            return dic
        except Exception as err:
            raise PaytefAPIError(menssage=err)

    def transaction_result_query(self, tcod):
        try:
            _url_request = "{}{}".format(CLOUD_URL, TRANSACTION_RESULT_URL)
            params = { "pinpad": tcod, }
            dic = self.__send_post_token_request__(_url_request, params).json()
            #print(dic)
            return dic
        except Exception as err:
            raise PaytefAPIError(menssage=err)

    def mifare_start_query(self, ppu, tcod):
        try:
            _url_request = "{}{}".format(CLOUD_URL, MIFARE_START_URL)
            params = {
                "executeOptions": {
                    "method": "polling"
                },
                "language": "es",
                "pinpad": tcod,
                "timeoutSeconds": 60
            }

            dic = self.__send_post_token_request__(_url_request, params).json()

            if self.update_token(dic, ppu):
                dic = self.__send_post_token_request__(_url_request, params).json()

            #print(dic)
            return dic["info"]["message"]
        except Exception as err:
            raise PaytefAPIError(menssage=err)

    def mifare_poll_query(self, tcod):
        try:
            _url_request = "{}{}".format(CLOUD_URL, MIFARE_POLL_URL)
            params = { "pinpad": tcod, }
            dic = self.__send_post_token_request__(_url_request, params).json()
            #print(dic)
            return dic
        except Exception as err:
            raise PaytefAPIError(menssage=err)

    def mifare_result_query(self, tcod):
        try:
            _url_request = "{}{}".format(CLOUD_URL, MIFARE_RESULT_URL)
            params = { "pinpad": tcod, }
            dic = self.__send_post_token_request__(_url_request, params).json()
            #print(dic)
            return dic
        except Exception as err:
            raise PaytefAPIError(menssage=err)


    def pinpad_status(self, ppu, tcod):
        try:
            #_url_request = "{}{}".format(API_URL, PINPAD_STATUS_URL)
            _url_request = "{}{}".format(CLOUD_URL, PINPAD_STATUS_URL)
            #print("--> GET STATUS")
            params = {
                "language": "es",
                "pinpad": tcod
                #"pinpad": "01853234265"
                #"pinpad": "19JQV5"
            }
            dic = self.__send_post_token_request__(_url_request, params).json()

            if self.update_token(dic, ppu):
                dic = self.__send_post_token_request__(_url_request, params).json()

            #print(dic)
            return dic
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

    def update_token(self, dic, ppu):
        if "error" in dic:
            if "description" in dic["error"] and "authorization token" in dic["error"]["description"]:
                ppu.token = self.get_token()
                ppu.save()
                self.token = ppu.token
                return True
        return False

'''
    FUNCTIONS
'''
def get_config(ppu):
    pt = Paytef(ppu.username, ppu.password, ppu.company, "", "")
    res = pt.config_query()
    print(res)
    return res
    #pt.transaction_query()
 
def get_token(ppu):
    #pt = Paytef("", "", "", "MS4yZmNp", "9KiyvtmGpVB9RHbLWvq4A494MwKbu2lfA5Zixdov")
    pt = Paytef("", "", "", ppu.accessKey, ppu.secretKey)
    pt.token = pt.get_token()
    print(pt.token)
    return pt.token

def get_status(ppu):
    pt = Paytef("", "", "", ppu.accessKey, ppu.secretKey, ppu.token)
    tcod = "19JQV5"
    #print("TOKEN: {}".format(pt.token))
    res = pt.pinpad_status(ppu, tcod)
    print(res)
    return res

def start_trans(ppu):
    import time 

    pt = Paytef("", "", "", ppu.accessKey, ppu.secretKey, ppu.token)
    tcod = ppu.tcod
    amount = 100
    ref = "Test transaction 01"
    session = pt.transaction_start_query(ppu, tcod, amount, ref)
    #print(session)

    trans_ok = False
    start_time = time.time()  # Guarda el momento de inicio
    timeout = 10  # Segundos
    res = ""
    while time.time() - start_time < timeout:
        #print("Ejecutando tarea...")  # Reemplaza con tu lógica
        time.sleep(1)  # Espera 1 segundo entre iteraciones (opcional)
        res = pt.transaction_poll_query(tcod)
        print("Confirmada: {}".format(res["info"]["transactionConfirmed"]))
        print("Estado: {}".format(res["info"]["transactionStatus"]))
        try:
            if res["info"]["transactionConfirmed"] == "true" and res["info"]["transactionStatus"] == "finished":
                trans_ok = True
                break
        except:
            pass

        #print(res)
        #print("¡Bucle terminado después de 10 segundos!")
    #print("OK")
    return trans_ok, res

def poll_trans():
    import time 

    pt = Paytef("", "", "", "MS4yZmNp", "9KiyvtmGpVB9RHbLWvq4A494MwKbu2lfA5Zixdov")
    pt.token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcHlJZCI6MTEzMjAyLCJpYXQiOjE3NTA5NDMzMzIsImV4cCI6MTc1MTAyOTczMiwiYXVkIjoidXJuOnBheXRlZjpkZXZpY2UtYXBpLWNsb3VkIiwiaXNzIjoidXJuOnBheXRlZjphd3MifQ.0IILCUwy92JbA6StXVB7PYYsRkCocJ0Ez16d2SXDO1Q"
    tcod = "19JQV5"
    res = pt.transaction_poll_query(tcod)
    print(res)
