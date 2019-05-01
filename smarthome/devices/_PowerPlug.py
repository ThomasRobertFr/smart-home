from flask_restful import Resource
from flask_restful import abort
from rpi_rf import RFDevice
from ..misc import config as _config
config = _config.get().rf


class PowerPlugs(Resource):
    def get(self):
        return PowerPlug.plugs


class PowerPlug(Resource):

    rfdevice = RFDevice(config.gpio_tx)
    rfdevice.enable_tx()

    plugs = {}

    for command in config.commands:
        # config format: [pulse, on, off, "plug", id]
        if len(command) >= 5 and command[3] == "plug":
            plugs[command[4]] = {
                "id": command[4],
                "pulse": command[0],
                "codes": (command[1], command[2]),
                "status": -1
            }

    @staticmethod
    def exists(id):
        if id not in PowerPlug.plugs:
            abort(404, message="Plug {} does not exist.".format(id))

    def get(self, id, status=None):
        if status == None:
            PowerPlug.exists(id)
            return PowerPlug.plugs[id]
        else:
            return self.put(id, status)

    def put(self, id, status):
        PowerPlug.exists(id)

        if status is True or status == "on":
            self.rfdevice.tx_code(PowerPlug.plugs[id]["codes"][0], 1, PowerPlug.plugs[id]["pulse"])
            PowerPlug.plugs[id]["status"] = 1
        else:
            self.rfdevice.tx_code(PowerPlug.plugs[id]["codes"][1], 1, PowerPlug.plugs[id]["pulse"])
            PowerPlug.plugs[id]["status"] = 0
