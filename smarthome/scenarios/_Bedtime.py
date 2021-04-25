import time

from . import Scenario
from ..devices import HueLamp, Devices


class Bedtime(Scenario):
    def run(self):
        devices = Devices()

        # Bedside: on + set color
        hue: HueLamp = devices.by_id["bedside"]
        hue.on()
        time.sleep(0.5)
        hue.hue_api_call({"on": True, "bri": 150, "xy": [0.5239,0.4136], "transitiontime": 3000})
