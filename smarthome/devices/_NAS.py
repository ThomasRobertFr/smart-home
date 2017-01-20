from flask_restful import Resource
import requests
from datetime import datetime, timedelta
import time
from RPi import GPIO
from ..misc import config as _config
config = _config.get().nas


class NAS(Resource):

    status = "unkn"
    status_time = datetime.now() - timedelta(days=100)

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(config.gpio, GPIO.OUT)
        GPIO.output(config.gpio, GPIO.HIGH)

    def get(self):
        # if starting, give it time
        if NAS.status == "starting" and (datetime.now() - NAS.status_time).total_seconds() < 130:
            return NAS.status
        if NAS.status == "shutdown" and (datetime.now() - NAS.status_time).total_seconds() < 60:
            return NAS.status

        try:
            requests.get(config.url, timeout=1)
            NAS.status = "on"
        except:
            NAS.status = "off"

        NAS.status_time = datetime.now()
        return NAS.status

    def put(self, status):
        if status == "on" and self.get() == "off":
            NAS.status = "starting"
            NAS.status_time = datetime.now()
            GPIO.output(config.gpio, GPIO.LOW)
            time.sleep(1)
            GPIO.output(config.gpio, GPIO.HIGH)

        elif status == "off" and self.get() == "on":
            NAS.status = "shutdown"
            NAS.status_time = datetime.now()
            GPIO.output(config.gpio, GPIO.LOW)
            time.sleep(7)
            GPIO.output(config.gpio, GPIO.HIGH)

# static GPIO init
GPIO.setmode(GPIO.BCM)
GPIO.setup(config.gpio, GPIO.OUT)
GPIO.output(config.gpio, GPIO.HIGH)
