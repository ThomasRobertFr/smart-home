import time

from . import Scenario
from ..devices import HueLamp, Devices


class Sleep(Scenario):
    def run(self):
        devices = Devices()

        # Bedside: initial color + transition
        hue: HueLamp = devices.by_id["bedside"]
        hue.on()

        for device_id in {"calendar", "dining-lamp", "couch-lamp", "desk"}:
            if device_id in devices.by_id:
                devices.by_id[device_id].off()

        time.sleep(1.5)
        hue.hue_api_call({"on": False, "bri": 0, "xy": [0.674, 0.322], "transitiontime": 450})
