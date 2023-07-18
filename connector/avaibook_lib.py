import requests
import hashlib
import time
import urllib
from .constants import *


class Avaibook():

    @classmethod
    def __send_request__(cls, _url_request, method='GET'):
        _headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        _response = requests.request(method, _url_request, headers=_headers)
        _response.raise_for_status()
        return _response

    @classmethod
    def __send_post_request__(cls, _url_request, dic):
        _headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        d = urllib.parse.urlencode(dic)
        _response = requests.post(_url_request, data=d, json=d, headers=_headers)
        _response.raise_for_status()
        return _response

    def __init__(self, accessToken=None):
        self.accessToken = accessToken
    
    def get_bookings(self,lockId=None):
        if not lockId:
            return 'Avantio API Error'

        #_url_request = LOCK_QUERY_URL.format(
        #    API_URI,
        #    LOCK_STATE_RESOURCE,
        #    self.clientId,
        #    self.accessToken,
        #    lockId,
        #    TTLock.__get_current_millis__(),
        #)
        _url_request = "https://api.avaibook.biz/api/partner/booking/bookings"
        return Avaibook.__send_request__(_url_request).json()


'''
    FUNCTIONS
'''
def get_booking_list(project_uuid):
    TOKEN = "43bedb65e2fa3a57dd19650c7f67a1cb648644f8"
    av = Avaibook(TOKEN)
    result = av.get_bookings()
    print(result)
    return result
