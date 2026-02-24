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
    API_URL = settings.OCTORADE_API_URL
except:
    API_URL = "https://api.octorate.com/connect/rest/v1"

LOGIN_URL = "/identity/apilogin"
TOKEN_URL = "/identity/token"

'''
    COMMONS
'''
def get_param(dic, key):
    return dic[key] if key in dic else ""

class OctoradeAPIError(Exception):
    def __init__(self, menssage='Invalid Parameter'):
        self.menssage=menssage

    def __str__(self):
        return 'Error: {}'.format(self.menssage)

class Octorade():
    def __init__(self, token=""):
        self.token = token
        self.ids = ""
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
            raise OctoradeAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise OctoradeAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise OctoradeAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise OctoradeAPIError(menssage=err)

    def __send_post_request__(self, _url_request, _json):
        try:
            _headers = {}
            #_headers['Accept'] = 'application/json'
            #_headers['x-api-key'] = '{}'.format(self.token)
            _headers['Content-Type'] = 'application/x-www-form-urlencoded'
            _response = requests.post(_url_request, headers=_headers, data=_json)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise OctoradeAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise OctoradeAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise OctoradeAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise OctoradeAPIError(menssage=err)

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
            raise OctoradeAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise OctoradeAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise OctoradeAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise OctoradeAPIError(menssage=err)


#    def get_bookings(self, status=CONFIRM_STATE):
#        try:
#            _url_request = "{}{}".format(API_URL, BOOKINGS_URL)
#            params = {
#                "includeAllRooms": "true",
#                "status": "confirmed"
#            }
#            dic = self.__send_request__(_url_request, params).json()
#            items = dic["data"]
#            return items
#        except Exception as err:
#            raise OctoradeAPIError(menssage=err)

    def get_token(self, client_id, client_secret, redirect_uri, code):
        try:
            #_url_request = "{}{}".format(API_URL, LOGIN_URL)
            #dic = self.__send_post_request__(_url_request, {"client_id":client_id, "client_secret":client_secret}).json()
            _url_request = "{}{}".format(API_URL, TOKEN_URL)
            payload = {
                "client_id": client_id, 
                "client_secret": client_secret,
                "redirect_uri": redirect_uri, 
                "code": code
            }
            dic = self.__send_post_request__(_url_request, payload).json()
            items = dic["data"]
            return items
        except Exception as err:
            raise OctoradeAPIError(menssage=err)


def get_token(pcu, ext_id):
    msg = ""
    oc = Octorade()
    client_id = "public_8a17175ce23b4f26888e3c2f1f355b9c"
    client_secret = "secret_efbdad0123d04470a9dac99228e139a0SXGFNUSURY"
    redirect_uri = "http%3A%2F%2Fpaddev.shidix.es%2Fconnector%2Foctorate%2Fupdate-token%2F'" 
    code = "487165"
    oc.get_token(client_id, client_secret, redirect_uri, code)
    #av = Octorade(pcu.token)
    #booking = av.get_booking(ext_id)
    #print(booking)
    return ""


