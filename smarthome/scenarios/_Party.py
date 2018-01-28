from flask_restful import Resource
from ..devices import PowerPlug, HueLamp
from ..sensors import State


class Party(Resource):

    actions = {
        "plugs": {
            "default": True,
            "title": "Turn plugs on",
            "config": {
                "plug-ids": ["main-lamp", "plasma-lamp", "starwars-lamp", "desk"]
            }
        },
        "hue": {
            "default": True,
            "title": "Turn Hue on",
            "config": {
                "ids": [1]
            }
        }
    }

    def get(self):
        return self.actions

    def put(self):
        print("=== PARTY ===")

        State().put("party")

        # PLUGS ON
        for plug in self.actions["plugs"]["config"]["plug-ids"]:
            PowerPlug().put(plug, "on")

        # HUE ON
        for id in self.actions["hue"]["config"]["ids"]:
            HueLamp().put(id, "on")

