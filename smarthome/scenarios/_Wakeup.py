from . import Scenario
from ..devices import Devices, HueLamp
import time


class Wakeup(Scenario):
    def run(self):
        devices = Devices()

        # Bedside: initial color + transition
        hue: HueLamp = devices.by_id["bedside"]
        hue.hue_api_call(
            {"on": True, "bri": 0, "xy": [0.674, 0.322], "transitiontime": 0}
        )
        time.sleep(1.5)
        hue.hue_api_call(
            {"on": True, "bri": 254, "xy": [0.4974, 0.4152], "transitiontime": 6000}
        )

        # Calendar
        devices.by_id["calendar"].set_level(10)
