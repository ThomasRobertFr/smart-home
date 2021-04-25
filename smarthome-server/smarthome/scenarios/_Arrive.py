from . import Scenario
from ..devices import Devices


class Arrive(Scenario):
    def run(self):
        devices = Devices()

        for device_id in {"calendar", "dining-lamp", "couch-lamp", "phone-charger"}:
            if device_id in devices.by_id:
                devices.by_id[device_id].on()
        devices.by_id["calendar"].set_level(10)
