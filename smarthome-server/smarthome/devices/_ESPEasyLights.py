import math
import requests

from smarthome.devices import Dimmer


class ESPEasyDimmer(Dimmer):
    def __init__(self, id: str, idx: int, host: str, gpio: int):
        super().__init__(id, idx)
        self.host = host
        self.gpio = gpio

    def on(self):
        requests.get(f"http://{self.host}/control?cmd=GPIO,{self.gpio},1")

    def off(self):
        requests.get(f"http://{self.host}/control?cmd=GPIO,{self.gpio},0")

    def set_level(self, value: float):
        requests.get(f"http://{self.host}/control?cmd=PWM,{self.gpio},{self.value_to_pwm(value)}")

    @staticmethod
    def value_to_pwm(value):
        """Transforms value in [1, 100] to a pwm in [1, 1024]"""
        return math.ceil((value / 100.) ** 2 * 1024)

    @staticmethod
    def pwm_to_value(pwm):
        """Reverse of value_to_pwm"""
        return math.ceil(math.sqrt(pwm / 1024.) * 100)
