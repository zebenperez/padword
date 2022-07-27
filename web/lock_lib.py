from django.conf import settings
from ttlockwrapper import TTLock

API_URI = 'https://api.ttlock.com/v3'
LOCK_PASSCODE_URL = '{}/{}?clientId={}&accessToken={}&lockId={}&keyboardPwd={}&startDate={}&endDate={}&addType=2&date={}'
ADD_PASSCODE_URL = '/keyboardPwd/add'
KEYBOARD_PWD_ID = 'keyboardPwdId'

class ShTTLock(TTLock):
    def lock_add_passcode(self,lockId=None,code="",startDate=0,endDate=0):
        if not lockId:
            raise TTlockAPIError()

        _url_request = LOCK_PASSCODE_URL.format(
            API_URI,
            ADD_PASSCODE_URL,
            self.clientId,
            self.accessToken,
            lockId,
            code,
            (startDate.timestamp() * 1000),
            (endDate.timestamp() * 1000),
            TTLock.__get_current_millis__(),
        )
        print(_url_request)
        return TTLock.__send_request__(_url_request).json().get(KEYBOARD_PWD_ID)

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
        print("--1-")
        self.ttlock.unlock(int(lock_id))
        print("-2-")

    def get_lock_state(self, lock_id):
        return self.ttlock.lock_state(lock_id)

    def get_lock_charge(self, lock_id):
        return self.ttlock.lock_electric_quantity(lock_id)

    def get_lock_code(self, lock_id, code, start_date, end_date):
        return self.ttlock.lock_add_passcode(lock_id, code, start_date, end_date)
