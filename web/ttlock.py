import requests
import hashlib
import time
import urllib
from .constants import *

def get_date(date):
    try:
        return int(round((date.timestamp() * 1000))) if date != 0 else 0
    except Exception as e:
        print(e)
        return 0

class TTlockAPIError(Exception):
    def __init__(self,error_code=-3,menssage='Invalid Parameter'):
        self.error_code = error_code
        self.menssage=menssage
    def __str__(self):
        return 'Error: {}'.format(self.menssage)
        #return 'Error returned from TTlockAPI: Error_code {} - {}'.format(self.error_code,self.menssage)

class TTLock():

    @classmethod
    def __is_erro_code_success__(cls,erroCode=None):
        if not erroCode and erroCode==0:
            return True
        else:
            return False

    @classmethod
    def __send_request__(cls, _url_request,method='GET'):
        _headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        _response = requests.request(method,_url_request, headers=_headers)
        _response.raise_for_status()
        if _response.json().get(ERROR_CODE_FIELD) :
            raise TTlockAPIError(error_code=_response.json().get(ERROR_CODE_FIELD),menssage=_response.json().get(MENSSAGE_FIELD))

        return _response

    @classmethod
    def __send_post_request__(cls, _url_request, dic):
        _headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        d = urllib.parse.urlencode(dic)
        _response = requests.post(_url_request, data=d, json=d, headers=_headers)
        _response.raise_for_status()
        if _response.json().get(ERROR_CODE_FIELD) :
            raise TTlockAPIError(error_code=_response.json().get(ERROR_CODE_FIELD),menssage=_response.json().get(MENSSAGE_FIELD))

        return _response

    @classmethod
    def create_user(cls,clientId,clientSecret,username,password):
        if (not password.islower()) or len(password)>32 or len(username)==0 or username.strip()=='':
            raise TTlockAPIError()

        _url_request = USER_CREATE_URL.format(
            API_URI,
            USER_RESOURCE,
            clientId,
            clientSecret,
            username,
            hashlib.md5(password.encode()).hexdigest(),
            TTLock.__get_current_millis__(),
        )

        return TTLock.__send_request__(_url_request).json()

    @classmethod
    def get_token(cls,clientId,clientSecret,username,password,redirect_uri):
        _url_request = TOKEN_CREATE_URL.format(
            TOKEN_RESOURCE,
            clientId,
            clientSecret,
            username,
            hashlib.md5(password.encode()).hexdigest(),
            redirect_uri,
        )

        return TTLock.__send_request__(_url_request,'POST').json()
    
    @classmethod
    def get_ext_token(cls,clientId,clientSecret,username,password):
        _url_request = TOKEN_EXT_CREATE_URL.format( TOKEN_RESOURCE,)
        dic = {CLIENT_ID:clientId, CLIENT_SECRET:clientSecret, USERNAME:username, PASSWORD:hashlib.md5(password.encode()).hexdigest()}

        return TTLock.__send_post_request__(_url_request, dic).json()
 
    @classmethod
    def refresh_token(cls,clientId,clientSecret,refresh,redirect_uri):
        _url_request = TOKEN_REFRESH_URL.format(
            TOKEN_RESOURCE,
            clientId,
            clientSecret,
            refresh,
            redirect_uri,
        )

        return TTLock.__send_request__(_url_request,'POST').json()

    @classmethod
    def refresh_ext_token(cls,clientId,clientSecret,refreshToken):
        _url_request = TOKEN_EXT_REFRESH_URL.format( TOKEN_RESOURCE,)
        dic = {CLIENT_ID:clientId, CLIENT_SECRET:clientSecret, GRANT_TYPE_FIELD:'refresh_token', REFRESH_TOKEN_FIELD:refreshToken}

        return TTLock.__send_post_request__(_url_request, dic).json()

    @classmethod
    def __verify_page__(cls,pageNo, totalPages):
        return pageNo<=totalPages
    
    @classmethod
    def __get_current_millis__(cls):
        return int(round(time.time() * 1000))

    def __init__(self, clientId=None,accessToken=None):
        self.clientId = clientId
        self.accessToken = accessToken
    
    def get_gateway_generator(self,pageSize=20):
        pageNo = 1
        totalPages = 1
        while TTLock.__verify_page__(pageNo, totalPages):
            _url_request = GATEWAY_LIST_URL.format(
                API_URI,
                GATEWAY_LIST_RESOURCE,
                self.clientId,
                self.accessToken,
                pageNo,
                pageSize,
                TTLock.__get_current_millis__(),
            )
            _response = TTLock.__send_request__(_url_request).json()
            for gateway in _response.get(LIST_FIELD):
                yield gateway
            totalPages = _response.get(PAGES_FIELD)
            pageNo=pageNo+1

    def get_locks_per_gateway_generator(self,gatewayId=None):
        if not gatewayId:
            raise TTlockAPIError()

        _url_request = LOCKS_PER_GATEWAY_URL.format(
            API_URI,
            LOCKS_PER_GATEWAY_RESOURCE,
            self.clientId,
            self.accessToken,
            gatewayId,
            TTLock.__get_current_millis__(),
        )
        
        for lock in TTLock.__send_request__(_url_request).json().get(LIST_FIELD):
            yield lock

    def get_lock_records_generator(self,lockId=None,pageSize=20,startDate=0,endDate=0):
        if not lockId:
            raise TTlockAPIError()

        pageNo = 1
        totalPages = 1
        while TTLock.__verify_page__(pageNo, totalPages):
            _url_request = LOCK_RECORDS_URL.format(
                API_URI,
                LOCK_RECORDS_RESOURCE,
                self.clientId,
                self.accessToken,
                lockId,
                pageNo,
                pageSize,
                startDate,
                endDate,
                TTLock.__get_current_millis__(),
            )
            _response = TTLock.__send_request__(_url_request).json()
            for records in _response.get(LIST_FIELD):
                yield records
            totalPages = _response.get(PAGES_FIELD)
            pageNo=pageNo+1
    
    def lock_state(self,lockId=None):
        if not lockId:
            raise TTlockAPIError()
        _url_request = LOCK_QUERY_URL.format(
            API_URI,
            LOCK_STATE_RESOURCE,
            self.clientId,
            self.accessToken,
            lockId,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(STATE_FIELD)

    def lock_electric_quantity(self,lockId=None):
        if not lockId:
            raise TTlockAPIError()
        _url_request = LOCK_QUERY_URL.format(
            API_URI,
            LOCK_ELECTRIC_QUANTITY_RESOURCE,
            self.clientId,
            self.accessToken,
            lockId,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(ELECTRIC_QUANTITY_FIELD)
    
    def lock(self,lockId=None):
        if not lockId:
            raise TTlockAPIError()

        _url_request = LOCK_QUERY_URL.format(
            API_URI,
            LOCK_RESOURCE,
            self.clientId,
            self.accessToken,
            lockId,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__is_erro_code_success__(TTLock.__send_request__(_url_request).json().get(ERROR_CODE_FIELD))

    def unlock(self,lockId=None):
        if not lockId:
            raise TTlockAPIError()

        _url_request = LOCK_QUERY_URL.format(
            API_URI,
            UNLOCK_RESOURCE,
            self.clientId,
            self.accessToken,
            lockId,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__is_erro_code_success__(TTLock.__send_request__(_url_request).json().get(ERROR_CODE_FIELD))

    #------------------------- SHIDIX --------------------------
    def lock_get_details(self, lockId=None):
        if not lockId:
            raise TTlockAPIError()

        _url_request = GET_LOCK_URL.format(
            API_URI,
            GET_LOCK_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json()

    def lock_get_all(self, pageNo=1, pageSize=100):
        _url_request = GET_ALL_LOCKS_URL.format(
            API_URI,
            GET_ALL_LOCKS_PREFIX_URL,
            self.clientId,
            self.accessToken,
            pageNo,
            pageSize,
            TTLock.__get_current_millis__(),
        )
        _response = TTLock.__send_request__(_url_request).json()
        for records in _response.get(LIST_FIELD):
            yield records

    def lock_get_gateway(self, lockId=None):
        if not lockId:
            raise TTlockAPIError()

        _url_request = GET_LOCK_GATEWAY_URL.format(
            API_URI,
            GET_LOCK_GATEWAY_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json()

    def lock_add_passcode(self, lockId=None, code="", name="", startDate=0, endDate=0):
        if not lockId:
            raise TTlockAPIError()

        _url_request = ADD_PASSCODE_URL.format(
            API_URI,
            ADD_PASSCODE_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            code,
            name,
            get_date(startDate),
            get_date(endDate),
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(KEYBOARD_PWD_ID)

    def lock_get_passcode(self, lockId=None, code_type="3", startDate=0, endDate=0):
        if not lockId:
            raise TTlockAPIError()

        _url_request = RANDOM_PASSCODE_URL.format(
            API_URI,
            RANDOM_PASSCODE_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            code_type,
            get_date(startDate),
            get_date(endDate),
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(KEYBOARD_PWD_ID)


    def lock_change_passcode(self, lockId=None, codeId="", newCode="", startDate=0, endDate=0):
        if not lockId:
            raise TTlockAPIError()

        _url_request = CHANGE_PASSCODE_URL.format(
            API_URI,
            CHANGE_PASSCODE_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            codeId,
            newCode,
            get_date(startDate),
            get_date(endDate),
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(ERROR_CODE_FIELD)

    def lock_remove_passcode(self, lockId=None, codeId=""):
        if not lockId:
            raise TTlockAPIError()

        _url_request = REMOVE_PASSCODE_URL.format(
            API_URI,
            REMOVE_PASSCODE_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            codeId,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(ERROR_CODE_FIELD)

    def lock_get_all_passcodes(self, lockId=None, pageNo=1, pageSize=100):
        if not lockId:
            raise TTlockAPIError()

        _url_request = GET_ALL_PASSCODE_URL.format(
            API_URI,
            GET_ALL_PASSCODE_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            pageNo,
            pageSize,
            TTLock.__get_current_millis__(),
        )
        _response = TTLock.__send_request__(_url_request).json()
        for records in _response.get(LIST_FIELD):
            yield records

    def lock_add_card(self, lockId=None, cardNumber="", cardName="", startDate=0, endDate=0):
        if not lockId:
            raise TTlockAPIError()

        _url_request = ADD_CARD_URL.format(
            API_URI,
            ADD_CARD_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            cardNumber,
            cardName,
            get_date(startDate),
            get_date(endDate),
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(CARD_ID)

    def lock_remove_card(self, lockId=None, codeId=""):
        if not lockId:
            raise TTlockAPIError()

        _url_request = REMOVE_CARD_URL.format(
            API_URI,
            REMOVE_CARD_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            codeId,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(ERROR_CODE_FIELD)

    def lock_get_all_cards(self, lockId=None, pageNo=1, pageSize=100):
        if not lockId:
            raise TTlockAPIError()

        _url_request = GET_ALL_CARD_URL.format(
            API_URI,
            GET_ALL_CARD_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            pageNo,
            pageSize,
            TTLock.__get_current_millis__(),
        )
        _response = TTLock.__send_request__(_url_request).json()
        for records in _response.get(LIST_FIELD):
            yield records

    def lock_change_period_card(self, lockId=None, cardId="", startDate=0, endDate=0):
        if not lockId:
            raise TTlockAPIError()

        _url_request = CHANGE_PERIOD_CARD_URL.format(
            API_URI,
            CHANGE_PERIOD_CARD_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            cardId,
            get_date(startDate),
            get_date(endDate),
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(ERROR_CODE_FIELD)

    def register_user(self, username, password, secret):
        _url_request = REGISTER_USER_URL.format(
            API_URI,
            REGISTER_USER_PREFIX_URL,
            self.clientId,
            secret,
            username,
            password,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(USERNAME)

    def delete_user(self, username, secret):
        _url_request = DELETE_USER_URL.format(
            API_URI,
            DELETE_USER_PREFIX_URL,
            self.clientId,
            secret,
            username,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json()
        #return TTLock.__send_request__(_url_request).json().get(ERROR_CODE_FIELD)

    def list_user(self, secret, pageNo=1, pageSize=100):
        _url_request = LIST_USER_URL.format(
            API_URI,
            LIST_USER_PREFIX_URL,
            self.clientId,
            secret,
            pageNo,
            pageSize,
            TTLock.__get_current_millis__(),
        )
        _response = TTLock.__send_request__(_url_request).json()
        for records in _response.get(LIST_FIELD):
            yield records

    def add_group(self, name=""):
        _url_request = ADD_GROUP_URL.format(
            API_URI,
            ADD_GROUP_PREFIX_URL,
            self.clientId,
            self.accessToken,
            name,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(GROUP_ID)

    def list_group(self):
        _url_request = LIST_GROUP_URL.format(
            API_URI,
            LIST_GROUP_PREFIX_URL,
            self.clientId,
            self.accessToken,
            TTLock.__get_current_millis__(),
        )
        _response = TTLock.__send_request__(_url_request).json()
        for records in _response.get(LIST_FIELD):
            yield records

    def set_lock_group(self, lockId=None, groupId=""):
        if not lockId:
            raise TTlockAPIError()

        _url_request = SET_LOCK_GROUP_URL.format(
            API_URI,
            SET_LOCK_GROUP_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            groupId,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(ERROR_CODE_FIELD)

    def delete_group(self, groupId):
        _url_request = DELETE_GROUP_URL.format(
            API_URI,
            DELETE_GROUP_PREFIX_URL,
            self.clientId,
            self.accessToken,
            groupId,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(ERROR_CODE_FIELD)

    def lock_send_key(self, lockId=None, receiverUsername="", keyName="", startDate=0, endDate=0):
        if not lockId:
            raise TTlockAPIError()

        _url_request = SEND_KEY_URL.format(
            API_URI,
            SEND_KEY_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            receiverUsername,
            keyName,
            get_date(startDate),
            get_date(endDate),
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request, "POST").json().get(KEY_ID)

    def lock_get_all_keys(self, lockId=None, pageNo=1, pageSize=100):
        if not lockId:
            raise TTlockAPIError()

        _url_request = GET_ALL_KEY_URL.format(
            API_URI,
            GET_ALL_KEY_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            pageNo,
            pageSize,
            TTLock.__get_current_millis__(),
        )
        _response = TTLock.__send_request__(_url_request).json()
        for records in _response.get(LIST_FIELD):
            yield records

    def lock_remove_key(self, lockId=None, keyId=""):
        if not lockId:
            raise TTlockAPIError()

        _url_request = REMOVE_KEY_URL.format(
            API_URI,
            REMOVE_KEY_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            keyId,
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(ERROR_CODE_FIELD)

    def lock_get_all_acc_keys(self, pageNo=1, pageSize=100):
        _url_request = GET_ALL_ACC_KEY_URL.format(
            API_URI,
            GET_ALL_ACC_KEY_PREFIX_URL,
            self.clientId,
            self.accessToken,
            pageNo,
            pageSize,
            TTLock.__get_current_millis__(),
        )
        _response = TTLock.__send_request__(_url_request).json()
        for records in _response.get(LIST_FIELD):
            yield records


