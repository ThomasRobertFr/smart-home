from flask_restful import Resource
from ..sensors import State
from ..devices import PowerPlug, HueLamp, Calendar


class Bedtime(Resource):

    actions = {
        "plugs": {
            "default": True,
            "title": "Turn plugs off",
            "config": {
                "plug-ids": ["dining-lamp", "couch-lamp", "desk"],
            }
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

        # PLUGS OFF

        for plug in self.actions["plugs"]["config"]["plug-ids"]:
            PowerPlug().put(plug, "off")
        print("> plugs off")

        Calendar().put("brightness", "3")

        # HUE TO ORANGE
        HueLamp().send(
            self.actions["light"]["config"]["hue-id"],
            {"on": True, "bri": 150, "xy": [0.5239,0.4136], "transitiontime": self.actions["light"]["options"]["duration"] * 10})
        print("> hue set for orange")
