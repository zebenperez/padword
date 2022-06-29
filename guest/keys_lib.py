from django.conf import settings
from ttlockwrapper import TTLock

class ShLock:
    def __init__(self):
        self.ttlock = TTLock(settings.TTLOCK_CLIENT, settings.TTLOCK_TOKEN)

    def get_locks(self, locks_id=[]):
        gateways = list(self.ttlock.get_gateway_generator())

        locks = []
        for gateway in gateways:
            locks += list(self.ttlock.get_locks_per_gateway_generator(gateway.get("gatewayId")))

        all_locks_id = [str(lock.get('lockId')) for lock in locks] 
        return [item for item in all_locks_id if item not in locks_id]

    def open_lock_by_id(self, lock_id):
        self.ttlock.unlock(int(lock_id))

