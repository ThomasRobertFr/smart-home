from flask_restful import Resource
from ..sensors import State
from ..devices import PowerPlug, RemotePilotWire, HueLamp, NAS
import time


class Sleep(Resource):

    actions = {
        "plugs": {
            "default": True,
            "title": "Turn plugs off",
            "config": {
                "plug-ids": ["main-lamp", "plasma-lamp", "starwars-lamp", "desk", "bathroom-heat"],
            }
        },
        "heating": {
            "default": True,
            "title": "Turn heating to eco mode"
        },
        "light": {
            "default": True,
            "title": "Turn bedside lamp off slowly",
            "config": {
                "hue-id": 1,
                "plug-id": "bedside-lamp"
            },
            "options": {
                "duration": 45
            }
        }
    }

    def get(self):
        return self.actions

    def put(self):
        print("=== SLEEP MODE ===")

        State().put("sleeping")

        # HUE ON

        hue_already_on = PowerPlug().get(self.actions["light"]["config"]["plug-id"])["status"] == 1
        PowerPlug().put(self.actions["light"]["config"]["plug-id"], "on")

        # PLUGS OFF

        for plug in self.actions["plugs"]["config"]["plug-ids"]:
            PowerPlug().put(plug, "off")
        print("> plugs off")

        # NAS OFF

        NAS().put("off")
        print("> NAS off")

        # HEATING ECO

        RemotePilotWire().put("eco")
        print("> heating eco")

        # HUE FADING

        if not hue_already_on:
            time.sleep(10)
        HueLamp().put(
            self.actions["light"]["config"]["hue-id"],
            {"on": False, "bri": 0, "xy": [0.674, 0.322],
             "transitiontime": self.actions["light"]["options"]["duration"] * 10})
        print("> hue set for red and off")

