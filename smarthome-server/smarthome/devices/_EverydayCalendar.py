import math

import requests

from smarthome.devices import Dimmer


class EverydayCalendar(Dimmer):
    def on(self):
        requests.put("http://raspi/calendar/display/switch/on")

    def off(self):
        requests.put("http://raspi/calendar/display/switch/off")

    def set_level(self, value: float):
        requests.put(f"http://raspi/calendar/display/brightness/{self.level_to_brigtness(value)}")
        requests.put("http://raspi/calendar/display/switch/on")

    @staticmethod
    def level_to_brigtness(level):
        """Transforms level in [1, 100] to a dimmerval in [1, 156]"""
        zero_one = (level / 100.) ** 2
        return math.ceil(zero_one * 256)
