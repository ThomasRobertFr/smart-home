import math

import requests

from smarthome.devices import Dimmer
from smarthome.misc import config as _config

config = _config.get().hue


class HueLamp(Dimmer):
    def __init__(self, id: str, idx: int, light_id: str):
        super().__init__(id, idx)
        self.light_id = light_id

    @property
    def url(self):
        return f"http://{config.host}/api/{config.username}/lights/{self.light_id}/state"

    def on(self):
        requests.put(self.url, json={"on": True})

    def off(self):
        requests.put(self.url, json={"on": False})

    def set_level(self, value: float):
        requests.put(self.url, json={"bri": math.floor(value / 100 * 255)})

    def hue_api_call(self, state: dict):
        requests.put(self.url, json=state)
