from django.conf import settings
from ttlockwrapper import TTLock

API_URI = 'https://api.ttlock.com/v3'
ADD_PASSCODE_URL = '{}/{}?clientId={}&accessToken={}&lockId={}&keyboardPwd={}&startDate={}&endDate={}&addType=2&date={}'
ADD_PASSCODE_PREFIX_URL = '/keyboardPwd/add'
CHANGE_PASSCODE_URL = '{}/{}?clientId={}&accessToken={}&lockId={}&keyboardPwdId={}&newKeyboardPwd={}&startDate={}&endDate={}&changeType=2&date={}'
CHANGE_PASSCODE_PREFIX_URL = '/keyboardPwd/change'
REMOVE_PASSCODE_URL = '{}/{}?clientId={}&accessToken={}&lockId={}&keyboardPwdId={}&deleteType=2&date={}'
REMOVE_PASSCODE_PREFIX_URL = '/keyboardPwd/delete'
GET_ALL_PASSCODE_URL = '{}/{}?clientId={}&accessToken={}&lockId={}&pageNo={}&pageSize={}&date={}'
GET_ALL_PASSCODE_PREFIX_URL = 'lock/listKeyboardPwd'

ADD_CARD_URL = '{}/{}?clientId={}&accessToken={}&lockId={}&cardNumber={}&startDate={}&endDate={}&addType=2&date={}'
#ADD_CARD_PREFIX_URL = '/identityCard/addForReversedCardNumber'
ADD_CARD_PREFIX_URL = '/identityCard/add'

LIST_FIELD = 'list'
KEYBOARD_PWD_ID = 'keyboardPwdId'
KEYBOARD_PWD = 'keyboardPwd'
CARD_ID = 'cardId'
ERROR_CODE_FIELD = 'errcode'

class ShTTLock(TTLock):
    def lock_add_passcode(self, lockId=None, code="", startDate=0, endDate=0):
        if not lockId:
            raise TTlockAPIError()

        _url_request = ADD_PASSCODE_URL.format(
            API_URI,
            ADD_PASSCODE_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            code,
            int(round((startDate.timestamp() * 1000))),
            int(round((endDate.timestamp() * 1000))),
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
            int(round((startDate.timestamp() * 1000))),
            int(round((endDate.timestamp() * 1000))),
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

    def lock_add_card(self, lockId=None, cardNumber="", startDate=0, endDate=0):
        if not lockId:
            raise TTlockAPIError()

        _url_request = ADD_CARD_URL.format(
            API_URI,
            ADD_CARD_PREFIX_URL,
            self.clientId,
            self.accessToken,
            lockId,
            cardNumber,
            int(round((startDate.timestamp() * 1000))),
            int(round((endDate.timestamp() * 1000))),
            TTLock.__get_current_millis__(),
        )
        return TTLock.__send_request__(_url_request).json().get(CARD_ID)


class ShLock:
    def __init__(self):
        self.ttlock = ShTTLock(settings.TTLOCK_CLIENT, settings.TTLOCK_TOKEN)

    def get_locks(self, locks_id=[]):
        gateways = list(self.ttlock.get_gateway_generator())

        locks = []
        for gateway in gateways:
            locks += list(self.ttlock.get_locks_per_gateway_generator(gateway.get("gatewayId")))

        all_locks_id = [str(lock.get('lockId')) for lock in locks] 
        return [item for item in all_locks_id if item not in locks_id]

    def open_lock_by_id(self, lock_id):
        try:
            return self.ttlock.unlock(int(lock_id))
        except Exception as e:
            return e

    def get_lock_state(self, lock_id):
        try:
            return self.ttlock.lock_state(lock_id)
        except Exception as e:
            return e

    def get_lock_charge(self, lock_id):
        try:
            return self.ttlock.lock_electric_quantity(lock_id)
        except Exception as e:
            return e

    def set_lock_code(self, lock_id, code, start_date, end_date):
        try:
            return self.ttlock.lock_add_passcode(lock_id, code, start_date, end_date)
        except Exception as e:
            return e

    def change_lock_code(self, lock_id, code_id, new_code, start_date, end_date):
        try:
            return self.ttlock.lock_change_passcode(lock_id, code_id, new_code, start_date, end_date)
        except Exception as e:
            return e

    def remove_lock_code(self, lock_id, code_id):
        try:
            return self.ttlock.lock_remove_passcode(lock_id, code_id)
        except Exception as e:
            return e

    def get_lock_all_passcodes(self, lock_id):
        try:
            return self.ttlock.lock_get_all_passcodes(lock_id)
        except Exception as e:
            return e

    def lock_add_card(self, lock_id, card_number, start_date, end_date):
        try:
            return self.ttlock.lock_add_card(lock_id, card_number, start_date, end_date)
        except Exception as e:
            return e


