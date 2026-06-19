from django.conf import settings
from datetime import datetime, timedelta
from .models import ProjectCaldeaUser

import requests
import json
import os

try:
    API_URL = settings.CALDEA_API_URL
except:
    API_URL = "http://api-padword.caldea.com"

TOKEN_URL = "/api/auth/token"

'''
    COMMONS
'''
def get_param(dic, key):
    return dic[key] if key in dic else ""

def write_log(result):
    f = open(os.path.join(settings.BASE_DIR, "caldea.log"), "a", encoding='utf-8')
    f.write("{}\n".format(result))
    f.close()

class CaldeaAPIError(Exception):
    def __init__(self, menssage='Invalid Parameter'):
        self.menssage=menssage

    def __str__(self):
        return 'Error: {}'.format(self.menssage)

class Caldea():
    def __init__(self, client_id, client_secret, token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = token
    
    def __send_request__(self, _url_request, _params=""):
        try:
            _headers = {}
            _headers['Accept'] = 'application/json'
            _headers['Authorization'] = 'Bearer {}'.format(self.token)
            if _params != "":
                _response = requests.get(_url_request, headers=_headers, params=_params)
                #print(_response.text)
            else:
                _response = requests.get(_url_request, headers=_headers)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise CaldeaAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise CaldeaAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise CaldeaAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise CaldeaAPIError(menssage=err)

    def __send_post_request__(self, _url_request, _json):
        try:
            _headers = {}
            _headers['Accept'] = 'application/json'
            #_headers['x-api-key'] = '{}'.format(self.token)
            _headers['Content-Type'] = 'application/json'
            _headers['User-Agent'] = 'Mozilla/5.0'
            print("--A--")
            print(_url_request)
            print(_headers)
            print(_json)
            _response = requests.post(_url_request, headers=_headers, data=_json)
            print(_response.text)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise CaldeaAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise CaldeaAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise CaldeaAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise CaldeaAPIError(menssage=err)

    def __send_post_token_request__(self, _url_request, _json):
        try:
            _headers = {}
            _headers['Authorization'] = 'Bearer {}'.format(self.token)
            _headers['Content-Type'] = 'application/json'
            _response = requests.patch(_url_request, headers=_headers, data=_json)
            #print(_response.text)
            #_response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise CaldeaAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise CaldeaAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise CaldeaAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise CaldeaAPIError(menssage=err)

    def get_token(self):
        try:
            _url_request = "{}{}".format(API_URL, TOKEN_URL)
            payload = {
                "client_id": self.client_id, 
                "client_secret": self.client_secret,
            }
            dic = self.__send_post_request__(_url_request, payload).json()
            items = dic["data"]
            return items
        except Exception as err:
            raise CaldeaAPIError(menssage=err)


'''
    FUNCTIONS
'''
#def get_token(pcu):
def get_token():
    msg = ""
    pcu = ProjectCaldeaUser.objects.filter(project_uuid="ccd38078-b710-eb58-b270-5926c27d9077").first()
    oc = Caldea(pcu.client_id, pcu.secret, pcu.token)
    oc.get_token()
    return ""

