from django.conf import settings
from datetime import datetime, timedelta
from web.models import Room
from guest.models import Guest
from padword.commons import new_ui_slug

import requests, json


try:
    API_URL = settings.ZKTECO_API_URL
except:
    API_URL = "https://zkbiocvs.zkteco.com/"

ADD_PERSON_URL = "api/person/add"


def get_param(dic, key):
    return dic[key] if key in dic else ""

class ZktecoAPIError(Exception):
    def __init__(self, menssage='Invalid Parameter'):
        self.menssage=menssage

    def __str__(self):
        return 'Error: {}'.format(self.menssage)

class Zkteco():
    def __init__(self, token):
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
            raise ZktecoAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise ZktecoAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise ZktecoAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise ZktecoAPIError(menssage=err)

    def __send_post_request__(self, _url_request, _json):
        try:
            _headers = {}
            _headers['Accept'] = 'application/json'
            #_headers['x-api-key'] = '{}'.format(self.token)
            _response = requests.post(_url_request, headers=_headers, json=_json, verify=False)
            print(_response.text)
            _response.raise_for_status()
            return _response
        except requests.exceptions.HTTPError as errh:
            raise ZktecoAPIError(menssage=errh)
        except requests.exceptions.ConnectionError as errc:
            raise ZktecoAPIError(menssage=errc)
        except requests.exceptions.Timeout as errt:
            raise ZktecoAPIError(menssage=errt)
        except requests.exceptions.RequestException as err:
            raise ZktecoAPIError(menssage=err)

    def add_person(self, idate, edate, level, band, lastname, name, pin):
        try:
            _url_request = "{}{}?access_token={}".format(API_URL, ADD_PERSON_URL, self.token)
            params = {
                "accEndTime": edate,
                "accLevelIds": level,
                "accStartTime": idate,
                "cardNo": band,
                "lastName": lastname,
                "name": name,
                "pin": pin                    
            }
            dic = self.__send_post_request__(_url_request, params).json()
            return dic
        except Exception as err:
            raise ZktecoAPIError(menssage=err)

'''
    FUNCTIONS
'''
def add_person(pzu, idate, edate, level, band, lastname, name, pin):
    zk = Zkteco(pzu.token)
    res = zk.add_person(idate, edate, level, band, lastname, name, pin)
    print(res)
    return res
 
