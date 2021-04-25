from . import Scenario
from ..devices import Devices


class Leave(Scenario):
    def run(self):
        devices = Devices()

        for device_id in {"bedside", "calendar", "dining-lamp", "couch-lamp", "desk"}:
            if device_id in devices.by_id:
                devices.by_id[device_id].off()
