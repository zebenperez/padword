from django.conf import settings
from .sensibo_client import SensiboClientAPI

class ShSensibo:
    def __init__(self, apiKey=""):
        self.client = SensiboClientAPI(apiKey)

    #--------------- Devices --------------
    def get_devices(self):
        return self.client.devices()

    def get_measurement(self, device_uid):
        return self.client.pod_measurement(device_uid)

    def get_ac_state(self, device_uid):
        return self.client.pod_ac_state(device_uid)

    def change_ac_state(self, device_uid, ac_state):
        return self.client.pod_change_ac_state(device_uid, ac_state, "on", not ac_state['on']) 

    def change_ac_state_param(self, device_uid, ac_state, param_name, param_value):
        return self.client.pod_change_ac_state(device_uid, ac_state, param_name, param_value) 

