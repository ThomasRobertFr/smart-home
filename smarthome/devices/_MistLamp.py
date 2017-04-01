from flask_restful import Resource
import subprocess
from ..misc import config as _config
config = _config.get().mist_lamp


class MistLamp(Resource):

    on = False

    def get(self):
        return MistLamp.on

    def put(self, command):
        if command == "on" or command == "off":
            MistLamp.on = True if command == "on" else "off"
            subprocess.call(["irsend", "SEND_ONCE", config.id, config.codes.power])
        if command == "bri":
            subprocess.call(["irsend", "SEND_ONCE", config.id, config.codes.brightness])
        if command == "light":
            subprocess.call(["irsend", "SEND_ONCE", config.id, config.codes.light])
        if command == "mist":
            subprocess.call(["irsend", "SEND_ONCE", config.id, config.codes.mist])
