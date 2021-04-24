from flask_restful import Resource
from ..devices import PowerPlug, Calendar
from ..sensors import State


class Arrive(Resource):

    actions = {
        "plugs": {
            "default": True,
            "title": "Turn plugs on",
            "config": {
                "plug-ids": ["dining-lamp", "couch-lamp", "phone-charger"]
            }
        }
    }

    def get(self):
        return self.actions

    def put(self):
        print("=== ARRIVE HOME ===")

        State().put("home")

        Calendar().put("brightness", "10")
        Calendar().put("switch", "on")

        # PLUGS ON
        for plug in self.actions["plugs"]["config"]["plug-ids"]:
            PowerPlug().put(plug, "on")



