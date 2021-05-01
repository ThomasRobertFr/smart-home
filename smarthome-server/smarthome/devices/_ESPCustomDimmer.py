import math

import requests

from . import Dimmer


class ESPCustomDimmer(Dimmer):
    def __init__(self, id: str, idx: int, host: str, min=0, max=1024):
        super().__init__(id, idx)
        self.host = host
        self.min = min
        self.max = max

    def off(self):
        requests.get(f"http://{self.host}/?off")

    def on(self):
        requests.get(f"http://{self.host}/?on&brightness={self.max}")

    def set_level(self, value: float):
        requests.get(f"http://{self.host}/?on&brightness={self.level_to_dimmerval(value)}")

    def level_to_dimmerval(self, level):
        """Transforms level in [1, 100] to a dimmerval in [1, 1024]"""
        zero_one = (level / 100.) ** 2
        return math.ceil(self.min + zero_one * (self.max - self.min))

    def dimmerval_to_level(self, dimmerval):
        """Reverse of level_to_dimmerval"""
        zero_one = dimmerval / (self.max - self.min) - self.min
        return math.ceil(math.sqrt(zero_one) * 100)


