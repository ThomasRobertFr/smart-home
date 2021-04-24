from flask_restful import Resource
import subprocess
from ..misc import config as _config, dotdict

config = _config.get().ir_remote
devices = {dev["id"]: dotdict.create_dot_dict(dev) for dev in config}
for x in devices.values():
    x.on = False


class IRRemote(Resource):
    devices = devices

    def get(self, id):
        return devices[id].on

    def put(self, id, command):
        if command == "on" or command == "off" or command == "power":
            command = "power"
            IRRemote.devices[id].on = not IRRemote.devices[id].on

        subprocess.call(["irsend", "SEND_ONCE", id, IRRemote.devices[id].codes[command]])
