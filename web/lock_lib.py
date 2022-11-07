from django.conf import settings
#from ttlockwrapper import TTLock
#from web.lock_lib_const import *
from web.ttlock import TTLock

class ShLock:
    def __init__(self, accessToken=""):
        self.clientId = settings.TTLOCK_CLIENT
        self.clientSecret = settings.TTLOCK_SECRET
        self.ttlock = TTLock(self.clientId, accessToken)

    #--------------- LOCKS --------------
    def get_locks(self, locks_id=[]):
        gateways = list(self.ttlock.get_gateway_generator())

        locks = []
        for gateway in gateways:
            locks += list(self.ttlock.get_locks_per_gateway_generator(gateway.get("gatewayId")))

        #all_locks_id = [str(lock.get('lockId')) for lock in locks] 
        all_locks_id = []
        for lock in locks:
            if str(lock.get('lockId')) not in all_locks_id:
                all_locks_id.append(str(lock.get('lockId')))

        return [item for item in all_locks_id if item not in locks_id]

    def get_lock_details(self, lock_id):
        try:
            return self.ttlock.lock_get_details(lock_id)
        except Exception as e:
            return e

    def get_lock_all(self):
        try:
            return self.ttlock.lock_get_all()
        except Exception as e:
            return e

    def get_lock_gateway(self, lock_id):
        try:
            return self.ttlock.lock_get_gateway(lock_id)
        except Exception as e:
            return e

    def open_lock_by_id(self, lock_id):
        try:
            return self.ttlock.unlock(int(lock_id))
        except Exception as e:
            print(e)
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

    #--------------- CODES --------------
    def set_lock_code(self, lock_id, code, name, start_date, end_date):
        try:
            return self.ttlock.lock_add_passcode(lock_id, code, name, start_date, end_date)
        except Exception as e:
            return e

    def get_lock_code(self, lock_id, code_type, start_date, end_date):
        try:
            return self.ttlock.lock_get_passcode(lock_id, code_type, start_date, end_date)
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

    #--------------- CARDS --------------
    def lock_add_card(self, lock_id, card_number, start_date, end_date):
        try:
            return self.ttlock.lock_add_card(lock_id, card_number, start_date, end_date)
        except Exception as e:
            return e

    def remove_lock_card(self, lock_id, code_id):
        try:
            return self.ttlock.lock_remove_card(lock_id, code_id)
        except Exception as e:
            return e

    def get_lock_all_cards(self, lock_id):
        try:
            return self.ttlock.lock_get_all_cards(lock_id)
        except Exception as e:
            return e

    def change_period_lock_card(self, lock_id, cardId, startDate, endDate):
        try:
            return self.ttlock.lock_change_period_card(lock_id, cardId, startDate, endDate)
        except Exception as e:
            return e

    #--------------- GROUPS --------------
    def add_group(self, name):
        try:
            return self.ttlock.add_group(name)
        except Exception as e:
            return e

    def list_group(self):
        try:
            return self.ttlock.list_group()
        except Exception as e:
            return e

    def set_lock_group(self, lock_id, group_id):
        try:
            return self.ttlock.set_lock_group(lock_id, group_id)
        except Exception as e:
            return e

    def delete_group(self, group_id):
        try:
            return self.ttlock.delete_group(group_id)
        except Exception as e:
            return e

    #--------------- EKEYS --------------
    def send_lock_key(self, lock_id, username, key_name, start_date, end_date):
        try:
            return self.ttlock.lock_send_key(lock_id, username, key_name, start_date, end_date)
        except Exception as e:
            return e

    def get_lock_all_keys(self, lock_id):
        try:
            return self.ttlock.lock_get_all_keys(lock_id)
        except Exception as e:
            return e

    def remove_lock_key(self, lock_id, key_id):
        try:
            return self.ttlock.lock_remove_key(lock_id, key_id)
        except Exception as e:
            return e


    #--------------- USERS --------------
    def get_token(self, username, password):
        try:
            return TTLock.get_ext_token(self.clientId, self.clientSecret, username, password)
        except Exception as e:
            return e

    #### FIXME: revisar esto
    def register_user(self, username, password):
        try:
            return self.ttlock.register_user(username, password, self.clientSecret)
        except Exception as e:
            return e

    def delete_user(self, username):
        try:
            return self.ttlock.delete_user(username, self.clientSecret)
        except Exception as e:
            return e

    def list_user(self):
        try:
            return self.ttlock.list_user(self.clientSecret)
        except Exception as e:
            return e


