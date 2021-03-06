from flask_restful import Resource
from ..sensors import State
from ..devices import PowerPlug, RemotePilotWire, HueLamp, Calendar
import time


class Bedtime(Resource):

    actions = {
        "plugs": {
            "default": True,
            "title": "Turn plugs off",
            "config": {
                "plug-ids": ["main-lamp", "plasma-lamp"],
            }
        },
        "heating": {
            "default": True,
            "title": "Turn heating to eco mode"
        },
        "light": {
            "default": True,
            "title": "Turn bedside lamp to a bedtime-friendly orange",
            "config": {
                "hue-id": 1
            },
            "options": {
                "duration": 300
            }
        }
    }

    def get(self):
        return self.actions

    def put(self):
        print("=== BEDTIME MODE ===")

        State().put("bedtime")

        # HUE ON
        HueLamp().put(self.actions["light"]["config"]["hue-id"], "on")
        #hue_already_on = PowerPlug().get(self.actions["light"]["config"]["plug-id"])["status"] == 1
        #PowerPlug().put(self.actions["light"]["config"]["plug-id"], "on")

        # PLUGS OFF

        for plug in self.actions["plugs"]["config"]["plug-ids"]:
            PowerPlug().put(plug, "off")
        print("> plugs off")

        # HEATING ECO

        RemotePilotWire().put("eco")
        print("> heating eco")

        Calendar().put("brightness", "3")

        # HUE TO ORANGE
        HueLamp().send(
            self.actions["light"]["config"]["hue-id"],
            {"on": True, "bri": 150, "xy": [0.5239,0.4136], "transitiontime": self.actions["light"]["options"]["duration"] * 10})
        print("> hue set for orange")
