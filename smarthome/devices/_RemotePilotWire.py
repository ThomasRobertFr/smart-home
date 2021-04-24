"""
from flask_restful import Resource
from ._PowerPlug import PowerPlug
from ..misc import config as _config
config = _config.get().remote_pilot_wire


class RemotePilotWire(Resource):

    ids = config.plug_ids

    def get(self):
        plug1 = PowerPlug().get(self.ids[0])["status"]
        plug2 = PowerPlug().get(self.ids[1])["status"]
        if plug1 == 1 and plug2 == 1:
            return "eco"
        if plug1 == 1 and plug2 < 1 or plug2 == 1 and plug1 < 1:
            return "off"
        else:
            return "on"

    def put(self, action):
        if action == "on":
            PowerPlug().put(self.ids[0], "off")
            PowerPlug().put(self.ids[1], "off")
        elif action == "eco":
            PowerPlug().put(self.ids[0], "on")
            PowerPlug().put(self.ids[1], "on")
        else:
            PowerPlug().put(self.ids[1], "off")
            PowerPlug().put(self.ids[0], "on")
"""
