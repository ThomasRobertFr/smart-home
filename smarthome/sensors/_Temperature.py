"""TODO debug temperature sensor
from flask_restful import Resource
import Adafruit_DHT
from ..misc import config as _config
config = _config.get().temperature


class Temperature(Resource):
    def get(self):
        humidity, temperature = Adafruit_DHT.read_retry(config.sensor, config.gpio)
        return {"humidity": humidity, "temperature": temperature}
"""
