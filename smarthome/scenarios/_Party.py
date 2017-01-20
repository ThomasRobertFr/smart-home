from flask_restful import Resource
from ..devices import PowerPlug
from ..sensors import State


class Party(Resource):

    actions = {
        "plugs": {
            "default": True,
            "title": "Turn plugs on",
            "config": {
                "plug-ids": ["main-lamp", "bedside-lamp", "plasma-lamp", "starwars-lamp", "desk"]
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



