# yapf: disable
try:
    from RPi import GPIO
except:
    import warnings; warnings.warn("Lib RPi not found, using mock for testing on a local machine")
    class GPIO:
        BCM = OUT = HIGH = LOW = False
        setmode = setup = output = lambda *args: False
# yapf: enable
import time

import requests

from smarthome.devices import Switch


class NAS(Switch):
    def __init__(self, id: str, idx: int, gpio: int, url: str):
        super().__init__(id, idx)
        self.gpio = gpio
        self.url = url
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio, GPIO.OUT)
        GPIO.output(self.gpio, GPIO.HIGH)

    def on(self):
        GPIO.output(self.gpio, GPIO.LOW)
        time.sleep(1)
        GPIO.output(self.gpio, GPIO.HIGH)

    def off(self):
        try:
            requests.get(self.url, timeout=2)
        except:
            raise ValueError("Could not find NAS running so did not stop it")
        else:
            GPIO.output(self.gpio, GPIO.LOW)
            time.sleep(7)
            GPIO.output(self.gpio, GPIO.HIGH)
