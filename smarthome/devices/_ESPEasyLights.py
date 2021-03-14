import math

import requests
from flask_restful import Resource
from flask_restful import abort
from ..misc import config as _config
config = _config.get().espeasylights


def value_to_pwm(value):
    """Transforms value in [0, 100] to a pwm in [0, 1024] with sqrt shape."""
    return round(math.sqrt(value) * 102.4)


def pwm_to_value(pwm):
    """Transforms pwm value in [0, 1024] to a value in [0, 100] with square shape."""
    return round((pwm / 102.4) ** 2)


class ESPEasyLights(Resource):

    @staticmethod
    def exists(id):
        if id not in config:
            abort(404, message="Light {} does not exist.".format(id))

    def get(self, id=None, status_or_value=None):
        if id is None:
            return {"_lights": config}
        try:
            data = requests.get(f"http://{config[id].ip}/control?cmd=status,gpio,{config[id].gpio}")
            data = data.json()
            if data["mode"] == "PWM":
                return {"mode": "dimmer", "status": pwm_to_value(data["state"])}
            else:
                return {"mode": "switch", "status": data["state"]}
        except Exception as e:
            abort(404, message="Problem with light {}: {}".format(id, e))

    def put(self, id, status_or_value):
        self.exists(id)
        switch = config[id]

        if switch["mode"] == "switch":
            if status_or_value not in ["on", "off"]:
                abort(403, message=f"Light {id} is a switch, pass 'on' or 'off'.")
            if status_or_value == "off":
                requests.get(f"http://{config[id].ip}/control?cmd=GPIO,{config[id].gpio},0")
            else:
                requests.get(f"http://{config[id].ip}/control?cmd=GPIO,{config[id].gpio},1")

        elif switch["mode"] == "dimmer":
            if status_or_value == "off":
                requests.get(f"http://{config[id].ip}/control?cmd=PWM,{config[id].gpio},0")
            elif status_or_value == "on":
                requests.get(f"http://{config[id].ip}/control?cmd=PWM,{config[id].gpio},1024")
            else:
                pwm = value_to_pwm(float(status_or_value))
                requests.get(f"http://{config[id].ip}/control?cmd=PWM,{config[id].gpio},{pwm}")

        else:
            abort(500, message=f"Wrongly configured light {id}, mode {switch['mode']} unknown")
