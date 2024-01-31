from django.conf import settings
from django.utils.translation import ugettext_lazy as _ 
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
            gateways = self.ttlock.lock_get_gateway(lock_id)
            val = ""
            for gateway in gateways.get('list'):
                val += "{}|{};".format(str(gateway.get("gatewayName")), str(gateway.get("rssi")))
            return val[:-1] if len(val) > 0 else val
            #return self.ttlock.lock_get_gateway(lock_id)
        except Exception as e:
            return e

    def get_lock_wifi(self, lock_id):
        try:
            wifi = self.ttlock.lock_get_wifi(lock_id)
            val = "{}|{};".format(str(wifi.get("networkName")), str(wifi.get("rssiGrade")))
            return val[:-1] if len(val) > 0 else val
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

    def get_lock_all_records(self, lock_id):
        records = list(self.ttlock.get_lock_records_generator(lock_id))
        return records

    #--------------- CODES --------------
    def set_lock_code(self, lock_id, code, name, start_date, end_date):
        try:
            return self.ttlock.lock_add_passcode(lock_id, code, name, start_date, end_date)
        except Exception as e:
            return e

    def get_lock_code(self, lock_id, code_type, start_date, end_date):
        try:
            print(lock_id)
            print(code_type)
            return self.ttlock.lock_get_passcode(lock_id, code_type, start_date, end_date)
        except Exception as e:
            print(e)
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
    def lock_add_card(self, lock_id, card_number, card_name, start_date, end_date):
        try:
            return self.ttlock.lock_add_card(lock_id, card_number, card_name, start_date, end_date)
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

    def refresh_token(self, refresh_token):
        try:
            return TTLock.refresh_ext_token(self.clientId, self.clientSecret, refresh_token)
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

    #--------------- GATEWAYS --------------
    def get_gateways(self):
        gateways = list(self.ttlock.get_gateway_generator())
        return gateways

    def get_gateway_locks(self, gateway_id):
        locks = list(self.ttlock.get_locks_per_gateway_generator(gateway_id))
        return locks

    def get_gateway_name(self, lock_id, gateway_id):
        try:
            gateways = self.ttlock.lock_get_gateway(lock_id)
            val = ""
            for gateway in gateways.get('list'):
                if str(gateway.get("gatewayId")) == str(gateway_id):
                    return gateway.get("gatewayName")
            return ""
        except Exception as e:
            return e

    #--------------- EKEYS --------------
    def get_ekeys(self):
        ekeys = list(self.ttlock.lock_get_all_acc_keys())
        return ekeys

def get_record_type(code):
    if code == 1:
        return _("Unlock by app")
    elif code == 4:
        return _("Unlock by passcode")
    elif code == 5:
        return _("Rise the lock")
    elif code == 6:
        return _("Lower the lock")
    elif code == 7:
        return _("Unlock by IC card")
    elif code == 8:
        return _("Unlock by fingerprint")
    elif code == 9:
        return _("Unlock by wrist strap")
    elif code == 10:
        return _("Unlock by Mechanical key")
    elif code == 11:
        return _("Lock by app")
    elif code == 12:
        return _("Unlock by gateway")
    elif code == 29:
        return _("Apply some force on the Lock")
    elif code == 30:
        return _("Door sensor closed")
    elif code == 31:
        return _("Door sensor open")
    elif code == 32:
        return _("Open from inside")
    elif code == 33:
        return _("Lock by fingerprint")
    elif code == 34:
        return _("Lock by passcode")
    elif code == 35:
        return _("Lock by IC card")
    elif code == 36:
        return _("Lock by Mechanical key")
    elif code == 37:
        return _("Remote Control")
    elif code == 42:
        return _("Received new local mail")
    elif code == 43:
        return _("Received new other cities mail")
    elif code == 44:
        return _("Tamper alert")
    elif code == 45:
        return _("Auto Lock")
    elif code == 46:
        return _("Unlock by unlock key")
    elif code == 47:
        return _("Lock by lock key")
    elif code == 48:
        return _("System locked ( Caused by, for example: Using INVALID Passcode/Fingerprint/Card several times)")
    elif code == 49:
        return _("Unlock by hotel card")
    elif code == 50:
        return _("Unlocked due to the high temperature")
    elif code == 52:
        return _("Dead lock with APP")
    elif code == 53:
        return _("Dead lock with passcode")
    elif code == 54:
        return _("The car left (for parking lock)")
    elif code == 55:
        return _("Unlock with key fob")
    elif code == 57:
        return _("Unlock with QR code success")
    elif code == 58:
        return _("Unlock with QR code failed, it's expired")
    elif code == 59:
        return _("Double locked")
    elif code == 60:
        return _("Cancel double lock")
    elif code == 61:
        return _("Lock with QR code success")
    elif code == 62:
        return _("Lock with QR code failed, the lock is double locked")
    elif code == 63:
        return _("Auto unlock at passage mode")
    else:
        return _("Unknown")
