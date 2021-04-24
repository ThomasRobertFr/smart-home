import math

import requests
from flask_restful import Resource
from flask_restful import abort
from ..misc import config as _config
config = _config.get().espcustomdimmer


def value_to_pwm(value, minpwm=0, maxpwm=1024):
    """Transforms value in [1, 100] to a pwm in [1, 1024]"""
    zero_one = (value / 100.) ** 2
    return math.ceil(minpwm + zero_one * (maxpwm - minpwm))


def pwm_to_value(pwm, minpwm=0, maxpwm=1024):
    """Reverse of value_to_pwm"""
    zero_one = pwm / (maxpwm - minpwm) - minpwm
    return math.ceil(math.sqrt(zero_one) * 100)


class ESPCustomDimmer(Resource):

    @staticmethod
    def exists(id):
        if id not in config:
            abort(404, message="Light {} does not exist.".format(id))

    def get(self, id=None, status_or_value=None):
        if id is None:
            return {"_lights": config}
        try:
            data = requests.get(f"http://{config[id].ip}/").json()
            data["brightness"] = pwm_to_value(data["brightness"])
            return data
        except Exception as e:
            abort(404, message=f"Problem with device {id}: {e}")

    def put(self, id, status_or_value):
        self.exists(id)

        if status_or_value == "off":
            requests.get(f"http://{config[id].ip}/?off")
        elif status_or_value == "on":
            requests.get(f"http://{config[id].ip}/?on")
        else:
            pwm = value_to_pwm(
                float(status_or_value),
                minpwm=config[id].get("min", 0),
                maxpwm=config[id].get("max", 1024)
            )
            requests.get(f"http://{config[id].ip}/?on&brightness={pwm}")
